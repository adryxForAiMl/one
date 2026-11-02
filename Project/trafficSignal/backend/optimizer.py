"""Constrained numerical optimization algorithms for adaptive traffic signal control.

Implements:
1. Webster's equisaturation method (analytical baseline).
2. Constrained numerical optimization via SciPy SLSQP.
3. Custom Projected Gradient Descent (PGD) with exact simplex and box constraints.
4. Objective function driven by Trapezoidal-integrated predicted queue delay.
5. Fail-safe fallback to validated signal timings on numerical divergence.
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from Traffic.config.settings import SignalTimingConfig
from Traffic.backend.numerical_methods import (
    trapezoidal_rule,
    project_onto_simplex_with_bounds,
    projected_gradient_descent,
    OptimizationConvergenceTrace,
)


@dataclass
class OptimizationResult:
    """Result returned by the signal optimizer."""
    green_times: np.ndarray          # Optimal green allocations [g_1, g_2, ...] in seconds
    cycle_length: float              # Total cycle duration (seconds)
    objective_value: float           # Minimum total delay or cost achieved
    solver_name: str                 # 'SLSQP', 'PGD', or 'Webster_Fallback'
    converged: bool                  # Whether numerical convergence criterion was satisfied
    iterations: int                  # Number of function/gradient evaluations
    is_fallback: bool                # True if fallback was triggered due to solver failure
    status_message: str              # Description of optimization outcome
    convergence_trace: Optional[OptimizationConvergenceTrace] = None


class TrafficSignalOptimizer:
    r"""Solves the constrained signal split optimization problem:
    
        min_{g} J(g) = \sum_{m=1}^M w_m \int_0^C q_m(t; g_m) dt
        s.t.  g_{m, min} \le g_m \le g_{m, max}     \forall m
              \sum_{m=1}^M g_m = C - L_total
    """

    def __init__(self, config: Optional[SignalTimingConfig] = None):
        self.config = config or SignalTimingConfig()
        
    def calculate_webster_split(
        self,
        approach_volumes: np.ndarray,
        saturation_flows: np.ndarray,
        cycle_length: Optional[float] = None
    ) -> np.ndarray:
        r"""Compute analytical Webster equisaturation green allocation:
            y_i = v_i / s_i
            Y = \sum y_i
            g_i = (y_i / Y) * C_eff
        """
        approach_volumes = np.asarray(approach_volumes, dtype=float)
        saturation_flows = np.asarray(saturation_flows, dtype=float)
        num_phases = len(approach_volumes)
        
        c = cycle_length if cycle_length is not None else self.config.default_cycle_length
        total_lost = num_phases * self.config.lost_time_per_phase
        effective_green = max(float(num_phases * self.config.min_green), c - total_lost)
        
        flow_ratios = np.maximum(0.01, approach_volumes) / np.maximum(0.1, saturation_flows)
        y_sum = np.sum(flow_ratios)
        
        if y_sum < 1e-6:
            # Equal split if zero traffic
            splits = np.full(num_phases, effective_green / num_phases)
        else:
            splits = (flow_ratios / y_sum) * effective_green
            
        # Clamp within [min_green, max_green] and project onto sum
        lb = np.full(num_phases, self.config.min_green)
        ub = np.full(num_phases, self.config.max_green)
        
        return project_onto_simplex_with_bounds(splits, effective_green, lb, ub)

    def _predict_phase_delay(
        self,
        start_green: float,
        end_green: float,
        q0: float,
        arrival_rate: float,
        sat_flow: float,
        cycle_length: float,
        dt: float = 1.0
    ) -> float:
        """Predict total vehicle delay for phase i over one cycle via Trapezoidal rule.
        
        Phase is green during [start_green, end_green); red during the remainder of [0, cycle_length).
        """
        steps = int(cycle_length / dt)
        q_history = np.zeros(steps + 1)
        t_history = np.linspace(0, cycle_length, steps + 1)
        
        q = max(0.0, q0)
        q_history[0] = q
        
        for k in range(steps):
            t = k * dt
            is_green = (start_green <= t < end_green)
            arrivals = arrival_rate * dt
            dep_cap = (sat_flow * dt) if is_green else 0.0
            actual_dep = min(q + arrivals, dep_cap)
            q = max(0.0, q + arrivals - actual_dep)
            q_history[k + 1] = q
            
        # Trapezoidal numerical integration of queue profile
        return trapezoidal_rule(q_history, t_history)

    def _objective_function(
        self,
        green_splits: np.ndarray,
        current_queues: np.ndarray,
        arrival_rates: np.ndarray,
        saturation_flows: np.ndarray,
        weights: np.ndarray,
        cycle_length: float
    ) -> float:
        """Total weighted intersection delay over one cycle horizon."""
        total_delay = 0.0
        lost = self.config.lost_time_per_phase
        current_start = 0.0
        
        for i in range(len(green_splits)):
            g_i = green_splits[i]
            start_g = current_start
            end_g = start_g + g_i
            current_start = end_g + lost
            
            delay_i = self._predict_phase_delay(
                start_green=start_g,
                end_green=end_g,
                q0=current_queues[i],
                arrival_rate=arrival_rates[i],
                sat_flow=saturation_flows[i],
                cycle_length=cycle_length
            )
            total_delay += weights[i] * delay_i
        return float(total_delay)

    def optimize_slsqp(
        self,
        current_queues: np.ndarray,
        arrival_rates: np.ndarray,
        saturation_flows: np.ndarray,
        weights: Optional[np.ndarray] = None,
        cycle_length: Optional[float] = None
    ) -> OptimizationResult:
        """Solve constrained signal timing using SciPy SLSQP."""
        current_queues = np.asarray(current_queues, dtype=float)
        arrival_rates = np.asarray(arrival_rates, dtype=float)
        saturation_flows = np.asarray(saturation_flows, dtype=float)
        num_phases = len(current_queues)
        
        if weights is None:
            weights = np.ones(num_phases, dtype=float)
            
        c = cycle_length if cycle_length is not None else self.config.default_cycle_length
        total_lost = num_phases * self.config.lost_time_per_phase
        effective_green = max(float(num_phases * self.config.min_green), c - total_lost)
        
        # Initial guess from analytical Webster model
        x0 = self.calculate_webster_split(arrival_rates * 3600.0, saturation_flows * 3600.0, c)
        
        # Bounds: min_green <= g_i <= max_green
        bounds = Bounds(
            lb=np.full(num_phases, self.config.min_green),
            ub=np.full(num_phases, self.config.max_green)
        )
        
        # Equality constraint: \sum g_i = effective_green
        constraint = LinearConstraint(
            A=np.ones((1, num_phases)),
            lb=effective_green,
            ub=effective_green
        )
        
        try:
            res = minimize(
                fun=lambda g: self._objective_function(
                    g, current_queues, arrival_rates, saturation_flows, weights, c
                ),
                x0=x0,
                method='SLSQP',
                bounds=bounds,
                constraints=[constraint],
                options={'maxiter': 100, 'ftol': 1e-4, 'disp': False}
            )
            
            if res.success and not np.isnan(res.fun):
                # Verify physical constraints
                clean_solution = project_onto_simplex_with_bounds(
                    res.x, effective_green,
                    np.full(num_phases, self.config.min_green),
                    np.full(num_phases, self.config.max_green)
                )
                return OptimizationResult(
                    green_times=clean_solution,
                    cycle_length=c,
                    objective_value=float(res.fun),
                    solver_name='SLSQP',
                    converged=True,
                    iterations=int(res.nit),
                    is_fallback=False,
                    status_message=f"SLSQP converged: {res.message}"
                )
            else:
                # Fallback to Webster split
                fallback_splits = x0
                cost = self._objective_function(
                    fallback_splits, current_queues, arrival_rates, saturation_flows, weights, c
                )
                return OptimizationResult(
                    green_times=fallback_splits,
                    cycle_length=c,
                    objective_value=cost,
                    solver_name='Webster_Fallback',
                    converged=False,
                    iterations=int(getattr(res, 'nit', 0)),
                    is_fallback=True,
                    status_message=f"SLSQP non-convergence fallback ({res.message})"
                )
        except Exception as e:
            # Unconditional safety fallback on unexpected numerical exception
            fallback_splits = x0
            cost = self._objective_function(
                fallback_splits, current_queues, arrival_rates, saturation_flows, weights, c
            )
            return OptimizationResult(
                green_times=fallback_splits,
                cycle_length=c,
                objective_value=cost,
                solver_name='Webster_Fallback',
                converged=False,
                iterations=0,
                is_fallback=True,
                status_message=f"Exception caught, activated safe fallback: {str(e)}"
            )

    def optimize_pgd(
        self,
        current_queues: np.ndarray,
        arrival_rates: np.ndarray,
        saturation_flows: np.ndarray,
        weights: Optional[np.ndarray] = None,
        cycle_length: Optional[float] = None
    ) -> OptimizationResult:
        """Solve constrained signal timing using Projected Gradient Descent (PGD).
        Provides full step-by-step convergence trace and gradient norms.
        """
        current_queues = np.asarray(current_queues, dtype=float)
        arrival_rates = np.asarray(arrival_rates, dtype=float)
        saturation_flows = np.asarray(saturation_flows, dtype=float)
        num_phases = len(current_queues)
        
        if weights is None:
            weights = np.ones(num_phases, dtype=float)
            
        c = cycle_length if cycle_length is not None else self.config.default_cycle_length
        total_lost = num_phases * self.config.lost_time_per_phase
        effective_green = max(float(num_phases * self.config.min_green), c - total_lost)
        
        lb = np.full(num_phases, self.config.min_green)
        ub = np.full(num_phases, self.config.max_green)
        
        # Initial guess
        x0 = np.full(num_phases, effective_green / num_phases)
        
        def cost_fn(g):
            return self._objective_function(
                g, current_queues, arrival_rates, saturation_flows, weights, c
            )
            
        def grad_fn(g):
            # Finite difference numerical gradient
            eps = 1e-4
            grad = np.zeros_like(g)
            for j in range(len(g)):
                g_plus = g.copy()
                g_plus[j] += eps
                g_minus = g.copy()
                g_minus[j] -= eps
                grad[j] = (cost_fn(g_plus) - cost_fn(g_minus)) / (2.0 * eps)
            return grad

        trace = projected_gradient_descent(
            cost_function=cost_fn,
            gradient_function=grad_fn,
            x0=x0,
            lower_bounds=lb,
            upper_bounds=ub,
            target_sum=effective_green,
            learning_rate=0.5,
            max_iterations=80,
            tolerance=1e-3
        )
        
        return OptimizationResult(
            green_times=trace.solution,
            cycle_length=c,
            objective_value=trace.final_objective,
            solver_name='PGD',
            converged=trace.converged,
            iterations=trace.iterations,
            is_fallback=not trace.converged,
            status_message=trace.message,
            convergence_trace=trace
        )
