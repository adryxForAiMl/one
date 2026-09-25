import { isEmail, isEmpty, isLength, isNumeric } from 'validator';

export const validateEmail = (email: string): boolean => {
    return isEmail(email);
};

export const validatePassword = (password: string): boolean => {
    return !isEmpty(password) && isLength(password, { min: 6 });
};

export const validateUsername = (username: string): boolean => {
    return !isEmpty(username) && isLength(username, { min: 3, max: 20 });
};

export const validatePhoneNumber = (phone: string): boolean => {
    return isNumeric(phone) && isLength(phone, { min: 10, max: 15 });
};

export const validateCreditCardNumber = (cardNumber: string): boolean => {
    return isNumeric(cardNumber) && isLength(cardNumber, { min: 13, max: 19 });
};