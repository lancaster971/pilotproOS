/**
 * MFA (Multi-Factor Authentication) Service
 * 
 * Battle-tested TOTP implementation using otpauth library
 * Compatible with Google Authenticator, Microsoft Authenticator, Authy
 */

import { TOTP, Secret } from 'otpauth';
import * as QRCode from 'qrcode';
import { DatabaseService } from './database.js';
import { randomBytes } from 'crypto';

export interface MFASetupResult {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

export interface MFAUserSettings {
  id: number;
  user_id: string;
  secret: string;
  backup_codes: string[];
  enabled: boolean;
  verified_at?: Date;
}

export class MFAService {
  private dbService: DatabaseService;

  constructor() {
    this.dbService = DatabaseService.getInstance();
  }

  /**
   * Generate MFA secret and QR code for user setup
   */
  async setupMFA(userId: string, userEmail: string): Promise<MFASetupResult> {
    try {
      // Generate a random secret
      const secret = new Secret({ size: 32 });
      
      // Create TOTP instance
      const totp = new TOTP({
        issuer: 'PilotProOS',
        label: userEmail,
        algorithm: 'SHA1',
        digits: 6,
        period: 30,
        secret: secret,
      });

      // Generate QR code
      const qrCodeUrl = await QRCode.toDataURL(totp.toString());
      
      // Generate backup codes
      const backupCodes = this.generateBackupCodes();

      // Save to database (disabled until verified)
      await this.saveMFASettings(userId, secret.base32, backupCodes, false);

      console.log('✅ MFA setup prepared for user:', userEmail);

      return {
        secret: secret.base32,
        qrCodeUrl,
        backupCodes,
      };
    } catch (error) {
      console.error('❌ MFA setup failed:', error);
      throw error;
    }
  }

  /**
   * Verify TOTP token during setup
   */
  async verifySetupToken(userId: string, token: string): Promise<boolean> {
    try {
      const mfaSettings = await this.getUserMFASettings(userId);
      if (!mfaSettings) {
        return false;
      }

      const isValid = this.verifyTOTPToken(mfaSettings.secret, token);
      
      if (isValid) {
        // Enable MFA after successful verification
        await this.enableMFA(userId);
        console.log('✅ MFA setup verified and enabled for user:', userId);
      }

      return isValid;
    } catch (error) {
      console.error('❌ MFA setup verification failed:', error);
      return false;
    }
  }

  /**
   * Verify TOTP token for authentication
   */
  async verifyAuthToken(userId: string, token: string): Promise<boolean> {
    try {
      const mfaSettings = await this.getUserMFASettings(userId);
      if (!mfaSettings || !mfaSettings.enabled) {
        return false;
      }

      // Check if it's a backup code
      if (this.isBackupCode(token)) {
        return await this.verifyBackupCode(userId, token);
      }

      // Verify TOTP token
      const isValid = this.verifyTOTPToken(mfaSettings.secret, token);
      
      if (isValid) {
        console.log('✅ MFA authentication successful for user:', userId);
      }

      return isValid;
    } catch (error) {
      console.error('❌ MFA authentication failed:', error);
      return false;
    }
  }

  /**
   * Verify TOTP token using otpauth
   */
  private verifyTOTPToken(secret: string, token: string): boolean {
    try {
      const totp = new TOTP({
        issuer: 'PilotProOS',
        algorithm: 'SHA1',
        digits: 6,
        period: 30,
        secret: Secret.fromBase32(secret),
      });

      // Validate token with time window tolerance
      const delta = totp.validate({
        token,
        window: 1, // Allow 1 step tolerance (30 seconds before/after)
      });

      return delta !== null;
    } catch (error) {
      console.error('❌ TOTP token verification error:', error);
      return false;
    }
  }

  /**
   * Generate backup codes
   */
  private generateBackupCodes(): string[] {
    const codes: string[] = [];
    for (let i = 0; i < 10; i++) {
      // Generate 8-character alphanumeric codes
      const code = randomBytes(4).toString('hex').toUpperCase();
      codes.push(code);
    }
    return codes;
  }

  /**
   * Check if token is a backup code format
   */
  private isBackupCode(token: string): boolean {
    // Backup codes are 8 character hex strings
    return /^[A-F0-9]{8}$/.test(token.toUpperCase());
  }

  /**
   * Verify backup code
   */
  private async verifyBackupCode(userId: string, code: string): Promise<boolean> {
    try {
      const mfaSettings = await this.getUserMFASettings(userId);
      if (!mfaSettings) {
        return false;
      }

      const backupCodes = mfaSettings.backup_codes;
      const upperCode = code.toUpperCase();

      if (backupCodes.includes(upperCode)) {
        // Remove used backup code
        const updatedCodes = backupCodes.filter(c => c !== upperCode);
        
        await this.dbService.query(`
          UPDATE pilotpros.user_mfa 
          SET backup_codes = $1, updated_at = CURRENT_TIMESTAMP
          WHERE user_id = $2
        `, [JSON.stringify(updatedCodes), userId]);

        console.log('✅ Backup code used successfully for user:', userId);
        return true;
      }

      return false;
    } catch (error) {
      console.error('❌ Backup code verification failed:', error);
      return false;
    }
  }

  /**
   * Get user MFA settings
   */
  async getUserMFASettings(userId: string): Promise<MFAUserSettings | null> {
    try {
      const settings = await this.dbService.getOne(`
        SELECT * FROM pilotpros.user_mfa WHERE user_id = $1
      `, [userId]);

      if (!settings) {
        return null;
      }

      return {
        ...settings,
        backup_codes: typeof settings.backup_codes === 'string' 
          ? JSON.parse(settings.backup_codes) 
          : settings.backup_codes || [],
      };
    } catch (error) {
      console.error('❌ Failed to get user MFA settings:', error);
      return null;
    }
  }

  /**
   * Save MFA settings to database
   */
  private async saveMFASettings(userId: string, secret: string, backupCodes: string[], enabled: boolean): Promise<void> {
    try {
      await this.dbService.query(`
        INSERT INTO pilotpros.user_mfa (user_id, secret, backup_codes, enabled)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
          secret = $2,
          backup_codes = $3,
          enabled = $4,
          updated_at = CURRENT_TIMESTAMP
      `, [userId, secret, JSON.stringify(backupCodes), enabled]);

    } catch (error) {
      console.error('❌ Failed to save MFA settings:', error);
      throw error;
    }
  }

  /**
   * Enable MFA for user
   */
  private async enableMFA(userId: string): Promise<void> {
    try {
      await this.dbService.query(`
        UPDATE pilotpros.user_mfa 
        SET enabled = true, verified_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
      `, [userId]);

      // Update user table
      await this.dbService.query(`
        UPDATE pilotpros.users 
        SET mfa_enabled = true, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
      `, [userId]);

    } catch (error) {
      console.error('❌ Failed to enable MFA:', error);
      throw error;
    }
  }

  /**
   * Disable MFA for user
   */
  async disableMFA(userId: string): Promise<void> {
    try {
      await this.dbService.query(`
        UPDATE pilotpros.user_mfa 
        SET enabled = false, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
      `, [userId]);

      await this.dbService.query(`
        UPDATE pilotpros.users 
        SET mfa_enabled = false, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
      `, [userId]);

      console.log('✅ MFA disabled for user:', userId);
    } catch (error) {
      console.error('❌ Failed to disable MFA:', error);
      throw error;
    }
  }

  /**
   * Generate new backup codes
   */
  async regenerateBackupCodes(userId: string): Promise<string[]> {
    try {
      const backupCodes = this.generateBackupCodes();
      
      await this.dbService.query(`
        UPDATE pilotpros.user_mfa 
        SET backup_codes = $1, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $2
      `, [JSON.stringify(backupCodes), userId]);

      console.log('✅ Backup codes regenerated for user:', userId);
      return backupCodes;
    } catch (error) {
      console.error('❌ Failed to regenerate backup codes:', error);
      throw error;
    }
  }

  /**
   * Check if user has MFA enabled
   */
  async isMFAEnabled(userId: string): Promise<boolean> {
    try {
      const settings = await this.getUserMFASettings(userId);
      return settings ? settings.enabled : false;
    } catch (error) {
      console.error('❌ Failed to check MFA status:', error);
      return false;
    }
  }
}

// Singleton pattern
let mfaServiceInstance: MFAService | null = null;

export function getMFAService(): MFAService {
  if (!mfaServiceInstance) {
    mfaServiceInstance = new MFAService();
  }
  return mfaServiceInstance;
}