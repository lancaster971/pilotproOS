-- Default Admin User Creation
-- Only creates admin if no users exist (first-time setup)

DO $$
BEGIN
    -- Check if any users exist
    IF NOT EXISTS (SELECT 1 FROM pilotpros.users LIMIT 1) THEN
        -- Create default admin user
        -- Password: PilotPro2025!
        -- Hash generated with bcryptjs (12 rounds)
        INSERT INTO pilotpros.users (
            email,
            password_hash,
            full_name,
            role,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            'admin@pilotpros.local',
            '$2a$12$K0ByDyMJG5y5ejrj7WZyv.0xXQXN3c0QLz8n9Y5tYq0NzxPZ1xTGi',
            'System Administrator',
            'admin',
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );

        RAISE NOTICE '✅ Default admin user created: admin@pilotpros.local';
        RAISE NOTICE '📝 Default password: PilotPro2025!';
        RAISE NOTICE '⚠️  Please change this password immediately in production!';
    ELSE
        RAISE NOTICE '✓ Users already exist, skipping admin creation';
    END IF;
END $$;

-- Also ensure we have at least one active user for development
-- This helps if users were soft-deleted
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pilotpros.users WHERE is_active = true LIMIT 1) THEN
        -- Reactivate the admin user if it was deactivated
        UPDATE pilotpros.users
        SET is_active = true,
            updated_at = CURRENT_TIMESTAMP
        WHERE email = 'admin@pilotpros.local';

        IF NOT FOUND THEN
            -- If admin doesn't exist at all, create it
            INSERT INTO pilotpros.users (
                email,
                password_hash,
                full_name,
                role,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                'admin@pilotpros.local',
                '$2a$12$K0ByDyMJG5y5ejrj7WZyv.0xXQXN3c0QLz8n9Y5tYq0NzxPZ1xTGi',
                'System Administrator',
                'admin',
                true,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
            RAISE NOTICE '✅ Admin user recreated after all users were deactivated';
        ELSE
            RAISE NOTICE '✅ Admin user reactivated';
        END IF;
    END IF;
END $$;