/**
 * Password Validation Utility
 * 
 * Simple but effective password requirements:
 * - Minimum 8 characters
 * - At least 1 uppercase letter
 * - At least 1 special character
 */

export class PasswordValidator {
  /**
   * Validate password strength
   */
  static validate(password) {
    const errors = [];

    if (!password || password.length < 8) {
      errors.push('Password deve avere almeno 8 caratteri');
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password deve contenere almeno una maiuscola');
    }

    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password deve contenere almeno un carattere speciale');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get password requirements text
   */
  static getRequirements() {
    return [
      'Almeno 8 caratteri',
      'Almeno una maiuscola (A-Z)',
      'Almeno un carattere speciale (!@#$%^&*)'
    ];
  }
}