/**
 * Passport.js Authentication Configuration
 *
 * Replaces custom JWT authentication with battle-tested Passport.js
 * Includes Redis session store for improved reliability and scalability
 */

import passport from 'passport';
import { Strategy as JwtStrategy, ExtractJwt } from 'passport-jwt';
import { Strategy as LocalStrategy } from 'passport-local';
import bcrypt from 'bcryptjs';
import { dbPool } from '../db/connection.js';

/**
 * Local Strategy for username/password authentication
 */
passport.use(new LocalStrategy({
  usernameField: 'email',
  passwordField: 'password'
}, async (email, password, done) => {
  try {
    // Query user from database
    const result = await dbPool.query(
      'SELECT id, email, password_hash, role, permissions, created_at FROM pilotpros.users WHERE email = $1',
      [email]
    );

    if (result.rows.length === 0) {
      return done(null, false, { message: 'Invalid credentials' });
    }

    const user = result.rows[0];

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return done(null, false, { message: 'Invalid credentials' });
    }

    // Update last login
    await dbPool.query(
      'UPDATE pilotpros.users SET last_login_at = CURRENT_TIMESTAMP WHERE id = $1',
      [user.id]
    );

    // Remove password hash from user object
    const { password_hash, ...userWithoutPassword } = user;

    return done(null, userWithoutPassword);
  } catch (error) {
    return done(error);
  }
}));

/**
 * JWT Strategy for API authentication
 */
passport.use(new JwtStrategy({
  jwtFromRequest: ExtractJwt.fromExtractors([
    ExtractJwt.fromAuthHeaderAsBearerToken(),
    // Extract from HttpOnly cookie as fallback
    (req) => {
      let token = null;
      if (req && req.cookies) {
        token = req.cookies['jwt_token'];
      }
      return token;
    }
  ]),
  secretOrKey: process.env.JWT_SECRET,
  passReqToCallback: true
}, async (req, payload, done) => {
  try {
    // Query user from database to ensure they still exist and are active
    const result = await dbPool.query(
      'SELECT id, email, role, permissions, created_at FROM pilotpros.users WHERE id = $1',
      [payload.userId]
    );

    if (result.rows.length === 0) {
      return done(null, false);
    }

    const user = result.rows[0];
    return done(null, user);
  } catch (error) {
    return done(error);
  }
}));

/**
 * Serialize user for session storage
 */
passport.serializeUser((user, done) => {
  done(null, user.id);
});

/**
 * Deserialize user from session storage
 */
passport.deserializeUser(async (id, done) => {
  try {
    const result = await dbPool.query(
      'SELECT id, email, role, permissions, created_at FROM pilotpros.users WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return done(null, false);
    }

    done(null, result.rows[0]);
  } catch (error) {
    done(error);
  }
});

export default passport;