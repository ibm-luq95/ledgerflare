/**
 * @fileoverview Custom error type definitions for robust error handling.
 * @module error-types
 */

/**
 * Base class for validation errors
 */
export class ValidationError extends Error {
  /**
   * Creates a validation error instance
   * @param {string} message - Human-readable error message
   */
  constructor(message) {
    super(message);
    this.name = "ValidationError";
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Base class for network-related errors
 */
export class NetworkError extends Error {
  /**
   * Creates a network error instance
   * @param {string} message - Error message
   * @param {number} [status=0] - HTTP status code if available
   * @param {*} [details=null] - Additional error details
   */
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = "NetworkError";
    this.status = status;
    this.details = details;
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/**
 * Base class for authentication/authorization errors
 */
export class AuthError extends Error {
  /**
   * Creates an auth error instance
   * @param {string} message - Error message
   */
  constructor(message) {
    super(message);
    this.name = "AuthError";
    Object.setPrototypeOf(this, AuthError.prototype);
  }
}
