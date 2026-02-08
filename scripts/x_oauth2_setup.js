#!/usr/bin/env node
import { createServer } from 'http';
import { parse } from 'url';
import { randomBytes, createHash } from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';

const execAsync = promisify(exec);

// Configuration
const PORT = 3000;
const REDIRECT_URI = `http://localhost:${PORT}/callback`;
const AUTH_URL = 'https://twitter.com/i/oauth2/authorize';
const TOKEN_URL = 'https://api.twitter.com/2/oauth2/token';

// Required scopes for full functionality
const SCOPES = [
  'tweet.read',
  'tweet.write',
  'users.read',
  'media.write',
  'tweet.moderate.write', // for deleting tweets
  'offline.access' // for refresh tokens
].join(' ');

// Generate PKCE parameters
function generatePKCE() {
  const verifier = randomBytes(32).toString('base64url');
  const challenge = createHash('sha256').update(verifier).digest('base64url');
  return { verifier, challenge };
}

// Generate random state
function generateState() {
  return randomBytes(16).toString('hex');
}

// Build authorization URL
function buildAuthUrl(clientId, state, codeChallenge) {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: REDIRECT_URI,
    scope: SCOPES,
    state: state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256'
  });

  return `${AUTH_URL}?${params.toString()}`;
}

// Exchange authorization code for tokens
async function exchangeCodeForTokens(code, codeVerifier, clientId, clientSecret) {
  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code: code,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier
  });

  const credentials = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const response = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${credentials}`
    },
    body: params.toString()
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Token exchange failed: ${error}`);
  }

  return response.json();
}

// Set environment variable permanently on the system
async function setEnvVariablePermanently(key, value) {
  const platform = process.platform;

  if (platform === 'win32') {
    // Windows - use setx command for user environment variable
    try {
      await execAsync(`setx ${key} "${value}"`);
      console.log(`  ✓ ${key} set in Windows user environment`);
    } catch (error) {
      console.error(`  ✗ Failed to set ${key}: ${error.message}`);
      throw error;
    }
  } else if (platform === 'darwin' || platform === 'linux') {
    // macOS or Linux
    const homeDir = os.homedir();
    let profileFile;

    // Determine which shell profile file to use
    const shell = process.env.SHELL || '';
    if (shell.includes('zsh')) {
      profileFile = path.join(homeDir, '.zshrc');
    } else if (shell.includes('bash')) {
      profileFile = path.join(homeDir, '.bashrc');
    } else {
      // Default to .bashrc
      profileFile = path.join(homeDir, '.bashrc');
    }

    try {
      const exportLine = `export ${key}="${value}"`;

      // Read existing file content
      let fileContent = '';
      try {
        fileContent = await fs.readFile(profileFile, 'utf8');
      } catch (error) {
        // File doesn't exist, will create it
      }

      // Check if variable already exists
      const regex = new RegExp(`^export ${key}=.*$`, 'gm');
      if (regex.test(fileContent)) {
        // Replace existing
        fileContent = fileContent.replace(regex, exportLine);
      } else {
        // Append new
        fileContent += `\n${exportLine}\n`;
      }

      await fs.writeFile(profileFile, fileContent);

      // Also set for current session
      process.env[key] = value;

      console.log(`  ✓ ${key} added to ${path.basename(profileFile)}`);
    } catch (error) {
      console.error(`  ✗ Failed to set ${key}: ${error.message}`);
      throw error;
    }
  }
}

// Save tokens to system environment variables
async function saveTokensToEnvironment(tokens) {
  console.log('\nSaving tokens to system environment variables...');

  const updates = {
    'X_ACCESS_TOKEN': tokens.access_token,
    'X_REFRESH_TOKEN': tokens.refresh_token || '',
    'X_TOKEN_EXPIRES_AT': new Date(Date.now() + (tokens.expires_in * 1000)).toISOString()
  };

  for (const [key, value] of Object.entries(updates)) {
    if (value) { // Only set if value exists
      await setEnvVariablePermanently(key, value);
    }
  }

  console.log('\n✓ All tokens saved to system environment variables');

  if (process.platform === 'win32') {
    console.log('\n⚠️  IMPORTANT: Restart your terminal for changes to take effect');
  } else {
    const shell = process.env.SHELL || '';
    const profileFile = shell.includes('zsh') ? '.zshrc' : '.bashrc';
    console.log(`\n⚠️  IMPORTANT: Run 'source ~/${profileFile}' or restart your terminal`);
  }
}

// Open url in browser
const openUrl = (url) => {
  const start = process.platform === 'darwin' ? 'open' :
    process.platform === 'win32' ? 'start' :
      'xdg-open';
  exec(`${start} ${url}`);
};

// Main setup flow
async function main() {
  console.log('X OAuth 2.0 Setup');
  console.log('======================\n');

  // Check for required credentials
  const clientId = process.env.X_CLIENT_ID;
  const clientSecret = process.env.X_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    console.error('Error: X_CLIENT_ID and X_CLIENT_SECRET must be set as environment variables');
    console.error('\nPlease set them first:');
    if (process.platform === 'win32') {
      console.error('  setx X_CLIENT_ID "your_client_id"');
      console.error('  setx X_CLIENT_SECRET "your_client_secret"');
    } else {
      console.error('  export X_CLIENT_ID="your_client_id"');
      console.error('  export X_CLIENT_SECRET="your_client_secret"');
    }
    process.exit(1);
  }

  console.log('Client ID:', clientId);
  console.log('Client Secret:', '***' + clientSecret.slice(-4));
  console.log('Redirect URI:', REDIRECT_URI);
  console.log('Scopes:', SCOPES.split(' ').join(', '));
  console.log();

  console.log('\n⚠️  IMPORTANT: Make sure your Twitter app has this EXACT callback URL:');
  console.log(`   ${REDIRECT_URI}`);
  console.log('\nTo add it:');
  console.log('1. Go to https://developer.twitter.com/en/portal/dashboard');
  console.log('2. Select your app → User authentication settings → Edit');
  console.log('3. Add the callback URL above (no trailing slash!)');
  console.log('4. Save and try again\n');

  // Generate PKCE and state
  const { verifier, challenge } = generatePKCE();
  const state = generateState();

  // Create authorization URL
  const authUrl = buildAuthUrl(clientId, state, challenge);

  // Create server to handle callback
  const server = createServer(async (req, res) => {
    const { pathname, query } = parse(req.url, true);

    if (pathname === '/callback') {
      const receivedState = query.state;
      const code = query.code;
      const error = query.error;

      if (error) {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<h1>Authorization Failed</h1><p>' + error + '</p>');
        server.close();
        console.error('Authorization failed:', error);
        process.exit(1);
      }

      if (receivedState !== state) {
        res.writeHead(400, { 'Content-Type': 'text/html' });
        res.end('<h1>Invalid State</h1><p>State mismatch - possible CSRF attack</p>');
        server.close();
        console.error('State mismatch!');
        process.exit(1);
      }

      if (code) {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<h1>Authorization Successful!</h1><p>You can close this window and return to the terminal.</p>');

        try {
          console.log('\nExchanging authorization code for tokens...');
          const tokens = await exchangeCodeForTokens(code, verifier, clientId, clientSecret);

          console.log('\nTokens received successfully!');
          console.log('Access Token:', tokens.access_token.substring(0, 20) + '...');
          if (tokens.refresh_token) {
            console.log('Refresh Token:', tokens.refresh_token.substring(0, 20) + '...');
          }
          console.log('Expires in:', tokens.expires_in, 'seconds');

          // Save to system environment variables
          await saveTokensToEnvironment(tokens);
          console.log('\nYou can now use OAuth 2.0 authentication in your Twitter MCP server!');

        } catch (error) {
          console.error('Failed to exchange code for tokens:', error);
        }

        server.close();
        process.exit(0);
      }
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  server.listen(PORT, () => {
    console.log(`\nCallback server listening on http://localhost:${PORT}`);
    console.log('\nOpening authorization URL in your browser...');
    console.log('If the browser doesn\'t open, visit this URL manually:');
    console.log(authUrl);
    console.log();

    openUrl(authUrl);

    // Debug: Show the parsed URL components
    if (process.env.DEBUG === 'true') {
      console.log('\nDebug - Authorization URL components:');
      const urlParts = new URL(authUrl);
      urlParts.searchParams.forEach((value, key) => {
        if (key === 'code_challenge') {
          console.log(`  ${key}: ${value.substring(0, 20)}...`);
        } else {
          console.log(`  ${key}: ${value}`);
        }
      });
    }
  });
}

// Run the setup
main().catch(console.error);
