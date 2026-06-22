## ADDED Requirements

### Requirement: User can login with username and password

The system SHALL provide a manual login endpoint that accepts `username` (6 chars) and `password` (6 chars). If the username does not exist, the system SHALL automatically create a new user account. If the username exists, the system SHALL verify the password using bcrypt.

#### Scenario: Successful login with existing account
- **WHEN** user sends POST to `/api/user/login/manual` with correct `username` and `password`
- **THEN** the system SHALL verify the password hash
- **AND** return a JWT token and user info

#### Scenario: Auto-register on first login
- **WHEN** user sends POST to `/api/user/login/manual` with a new `username` and `password`
- **THEN** the system SHALL create a new user with hashed password
- **AND** return a JWT token and user info

#### Scenario: Wrong password
- **WHEN** user sends POST to `/api/user/login/manual` with existing `username` but wrong `password`
- **THEN** the system SHALL return `{ "success": false, "error": "密码错误" }`

### Requirement: User can logout
The system SHALL allow logged-in users to log out from the profile page.

#### Scenario: User clicks logout
- **WHEN** user clicks "退出登录" button on profile page
- **THEN** the system SHALL clear the stored token and user info
- **AND** refresh the profile page to show unauthenticated state
