import { useState } from "react"

import {
  ShieldAlert,
  Server,
  Database,
  UserRound,
  X,
} from "lucide-react"

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from "@xyflow/react"

import "@xyflow/react/dist/style.css"

type Finding = {
  id?: string
  endpoint: string
  method: string
  attacker: string
  resource_owner: string
  object_id: number
}

type SecurityNodeData = {
  label: string
  subtitle: string
  variant: "attacker" | "api" | "object" | "owner"
}

type AttackGraphProps = {
  finding: Finding | null
}

function SecurityNode({
  data,
}: {
  data: SecurityNodeData
}) {
  const styles = {
    attacker: {
      border: "border-red-500/60",
      icon: "bg-red-500/10",
      text: "text-red-400",
    },

    api: {
      border: "border-cyan-500/60",
      icon: "bg-cyan-500/10",
      text: "text-cyan-400",
    },

    object: {
      border: "border-amber-500/60",
      icon: "bg-amber-500/10",
      text: "text-amber-400",
    },

    owner: {
      border: "border-emerald-500/60",
      icon: "bg-emerald-500/10",
      text: "text-emerald-400",
    },
  }

  const style = styles[data.variant]

  return (
    <div
      className={`
        min-w-[190px]
        cursor-pointer
        rounded-xl
        border
        ${style.border}
        bg-slate-900
        px-4
        py-3
        shadow-xl
        transition-all
        duration-200
        hover:-translate-y-1
        hover:scale-[1.02]
        hover:border-cyan-400
        hover:bg-slate-800
        hover:shadow-cyan-500/10
      `}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!border-slate-950 !bg-slate-500"
      />

      <div className="flex items-center gap-3">

        <div
          className={`
            flex
            h-10
            w-10
            shrink-0
            items-center
            justify-center
            rounded-lg
            ${style.icon}
          `}
        >
          {data.variant === "attacker" && (
            <UserRound
              size={19}
              className="text-red-400"
            />
          )}

          {data.variant === "api" && (
            <Server
              size={19}
              className="text-cyan-400"
            />
          )}

          {data.variant === "object" && (
            <Database
              size={19}
              className="text-amber-400"
            />
          )}

          {data.variant === "owner" && (
            <ShieldAlert
              size={19}
              className="text-emerald-400"
            />
          )}
        </div>

        <div className="min-w-0">

          <p
            className={`
              truncate
              text-sm
              font-semibold
              ${style.text}
            `}
          >
            {data.label}
          </p>

          <p className="mt-1 truncate text-xs text-slate-500">
            {data.subtitle}
          </p>

        </div>

      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!border-slate-950 !bg-slate-500"
      />
    </div>
  )
}

const nodeTypes = {
  security: SecurityNode,
}

export default function AttackGraph({
  finding,
}: AttackGraphProps) {

  const [selectedNode, setSelectedNode] =
    useState<SecurityNodeData | null>(null)

  const attacker =
    finding?.attacker ?? "User A"

  const resourceOwner =
    finding?.resource_owner ?? "User B"

  const endpoint =
    finding?.endpoint ?? "/orders/102"

  const method =
    finding?.method ?? "GET"

  const objectId =
    finding?.object_id ?? 102

  const nodes: Node<SecurityNodeData>[] = [
    {
      id: "attacker",
      type: "security",
      position: {
        x: 40,
        y: 170,
      },
      data: {
        label: attacker,
        subtitle: "Attacker",
        variant: "attacker",
      },
    },

    {
      id: "api",
      type: "security",
      position: {
        x: 330,
        y: 170,
      },
      data: {
        label: "API Gateway",
        subtitle: `${method} ${endpoint}`,
        variant: "api",
      },
    },

    {
      id: "object",
      type: "security",
      position: {
        x: 620,
        y: 170,
      },
      data: {
        label: `Order #${objectId}`,
        subtitle: "Protected Object",
        variant: "object",
      },
    },

    {
      id: "owner",
      type: "security",
      position: {
        x: 910,
        y: 170,
      },
      data: {
        label: resourceOwner,
        subtitle: "Resource Owner",
        variant: "owner",
      },
    },
  ]

  const edges: Edge[] = [
    {
      id: "attacker-api",
      source: "attacker",
      target: "api",
      label: `${method} ${endpoint}`,
      animated: true,
      style: {
        stroke: "#ef4444",
        strokeWidth: 2,
      },
      labelStyle: {
        fill: "#94a3b8",
        fontSize: 11,
      },
    },

    {
      id: "api-object",
      source: "api",
      target: "object",
      label: "Unauthorized access",
      animated: true,
      style: {
        stroke: "#f59e0b",
        strokeWidth: 2,
      },
      labelStyle: {
        fill: "#94a3b8",
        fontSize: 11,
      },
    },

    {
      id: "object-owner",
      source: "object",
      target: "owner",
      label: "Owned by",
      style: {
        stroke: "#22c55e",
        strokeWidth: 2,
      },
      labelStyle: {
        fill: "#94a3b8",
        fontSize: 11,
      },
    },
  ]

  const handleNodeClick: NodeMouseHandler = (
    _event,
    node
  ) => {
    setSelectedNode(
      node.data as SecurityNodeData
    )
  }

  return (
    <div className="relative isolate h-[520px] w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950">

      <ReactFlow
        key={`${attacker}-${resourceOwner}-${objectId}-${endpoint}`}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{
          padding: 0.25,
        }}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={true}
        onNodeClick={handleNodeClick}
      >

        <Background
          gap={20}
          size={1}
          color="#1e293b"
        />

        <Controls />

        <MiniMap
          nodeColor={(node) => {

            if (node.id === "attacker") {
              return "#ef4444"
            }

            if (node.id === "api") {
              return "#06b6d4"
            }

            if (node.id === "object") {
              return "#f59e0b"
            }

            return "#22c55e"
          }}
          maskColor="rgba(2, 6, 23, 0.75)"
        />

      </ReactFlow>

      {selectedNode && (

        <div
          className="
            pointer-events-auto
            absolute
            right-4
            top-4
            z-[100]
            w-80
            rounded-xl
            border
            border-cyan-500/40
            bg-slate-950
            p-5
            shadow-2xl
            shadow-black/60
            backdrop-blur-xl
          "
        >

          <div className="flex items-start justify-between">

            <div>

              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-400">
                Attack Graph Node
              </p>

              <h4 className="mt-1 text-lg font-bold text-white">
                {selectedNode.label}
              </h4>

            </div>

            <button
              type="button"
              onClick={() => setSelectedNode(null)}
              className="
                flex
                h-7
                w-7
                items-center
                justify-center
                rounded-md
                text-slate-500
                transition
                hover:bg-slate-800
                hover:text-white
              "
            >
              <X size={16} />
            </button>

          </div>

          <div className="mt-5 space-y-3">

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">

              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Node Type
              </p>

              <p className="mt-1 text-sm font-medium capitalize text-slate-200">
                {selectedNode.variant}
              </p>

            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">

              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Description
              </p>

              <p className="mt-1 text-sm text-slate-300">
                {selectedNode.subtitle}
              </p>

            </div>

            {selectedNode.variant === "attacker" && (

              <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-3">

                <p className="text-[10px] font-semibold uppercase tracking-wider text-red-400">
                  Security Role
                </p>

                <p className="mt-1 text-sm font-semibold text-red-300">
                  Authenticated Attacker
                </p>

                <p className="mt-2 text-xs leading-5 text-slate-400">
                  This identity successfully crossed the authorization boundary.
                </p>

              </div>

            )}

            {selectedNode.variant === "api" && (

              <div className="rounded-lg border border-cyan-900/50 bg-cyan-950/20 p-3">

                <p className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400">
                  Attack Surface
                </p>

                <p className="mt-1 font-mono text-sm text-slate-200">
                  {method} {endpoint}
                </p>

                <p className="mt-2 text-xs leading-5 text-slate-400">
                  Endpoint accepted an authenticated request without enforcing object ownership.
                </p>

              </div>

            )}

            {selectedNode.variant === "object" && (

              <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3">

                <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
                  Access Status
                </p>

                <p className="mt-1 text-sm font-semibold text-amber-300">
                  Unauthorized Access
                </p>

                <p className="mt-2 text-xs leading-5 text-slate-400">
                  Object #{objectId} belongs to another authenticated user.
                </p>

              </div>

            )}

            {selectedNode.variant === "owner" && (

              <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-3">

                <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400">
                  Resource Role
                </p>

                <p className="mt-1 text-sm font-semibold text-emerald-300">
                  Resource Owner
                </p>

                <p className="mt-2 text-xs leading-5 text-slate-400">
                  This user owns the protected object shown in the attack path.
                </p>

              </div>

            )}

          </div>

        </div>

      )}

    </div>
  )
}