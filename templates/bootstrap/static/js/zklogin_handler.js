// zklogin_handler.js

// Import necessary functions from Sui SDK via CDN ESM modules
import { Ed25519Keypair } from 'https://cdn.jsdelivr.net/npm/@mysten/sui@1.29.1/keypairs/ed25519/+esm';
import { SuiClient, getFullnodeUrl } from 'https://cdn.jsdelivr.net/npm/@mysten/sui@1.29.1/client/+esm';
import { generateNonce, generateRandomness, jwtToAddress } from 'https://cdn.jsdelivr.net/npm/@mysten/sui@1.29.1/zklogin/+esm';
import { fromB64 } from 'https://cdn.jsdelivr.net/npm/@mysten/sui@1.29.1/utils/+esm';

// These should be configurable, perhaps fetched from backend or set in a config script
const GOOGLE_CLIENT_ID = "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com"; // Replace with actual Client ID from Google Cloud Console
const REDIRECT_URI = window.location.origin + "/auth/zklogin/callback"; // Ensure this route is handled by your FastAPI app

// Sui RPC endpoint
const SUI_NETWORK = 'testnet'; // or 'devnet', 'mainnet'
const suiClient = new SuiClient({ url: getFullnodeUrl(SUI_NETWORK) });

document.addEventListener('DOMContentLoaded', () => {
    const zkLoginButton = document.getElementById('zklogin_google_button');
    if (zkLoginButton) {
        zkLoginButton.addEventListener('click', startZkLoginWithGoogle);
    } else {
        console.warn('zkLogin Google button not found. Ensure it has id="zklogin_google_button".');
    }

    // Handle callback if this is the redirect URI page
    if (window.location.pathname === "/auth/zklogin/callback") { 
        handleZkLoginCallback();
    }
});

async function startZkLoginWithGoogle() {
    console.log('zkLogin with Google initiated.');
    if (GOOGLE_CLIENT_ID === "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com") {
        alert("Google Client ID is not configured in zklogin_handler.js. Please configure it first.");
        return;
    }

    try {
        // 1. Generate ephemeral keypair
        const ephemeralKeyPair = new Ed25519Keypair();
        const ephemeralPublicKey = ephemeralKeyPair.getPublicKey();
        console.log("Ephemeral Public Key (Sui format):", ephemeralPublicKey.toSuiPublicKey());

        // Store ephemeral secret key (base64) securely (e.g., sessionStorage for this session only)
        sessionStorage.setItem('zklogin_ephemeral_secret_key_b64', ephemeralKeyPair.export().privateKey);

        // 2. Get current epoch from a Sui RPC endpoint
        const { epoch } = await suiClient.getLatestSuiSystemState();
        console.log("Current epoch:", epoch);

        // 3. Define maxEpoch (e.g., current epoch + 2 or 3)
        const maxEpoch = parseInt(epoch) + 2;

        // 4. Generate randomness for nonce
        const jwtRandomness = generateRandomness();
        sessionStorage.setItem('zklogin_jwt_randomness', jwtRandomness);
        console.log("JWT Randomness:", jwtRandomness);

        // 5. Generate nonce
        const nonce = generateNonce(ephemeralPublicKey, maxEpoch, jwtRandomness);
        console.log("Nonce:", nonce);

        // 6. Construct Google OAuth URL
        const params = new URLSearchParams({
            client_id: GOOGLE_CLIENT_ID,
            redirect_uri: REDIRECT_URI,
            response_type: 'id_token', // zkLogin requires id_token
            scope: 'openid email profile',
            nonce: nonce,
        });

        const googleOAuthURL = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
        console.log("Redirecting to Google OAuth URL:", googleOAuthURL);

        // 7. Redirect the user to the Google OAuth URL
        window.location.href = googleOAuthURL;

    } catch (error) {
        console.error("Error during zkLogin initiation:", error);
        alert("Failed to initiate Google login. Check console for details.");
    }
}

async function handleZkLoginCallback() {
    console.log('Handling zkLogin callback.');
    try {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const id_token = params.get('id_token');

        if (!id_token) {
            console.error('ID Token not found in URL fragment.');
            alert('Login callback error: ID Token not found.');
            window.location.href = "/"; // Or login page
            return;
        }
        console.log('ID Token received.');

        const ephemeralSecretKeyB64 = sessionStorage.getItem('zklogin_ephemeral_secret_key_b64');
        const jwtRandomness = sessionStorage.getItem('zklogin_jwt_randomness');

        if (!ephemeralSecretKeyB64 || !jwtRandomness) {
            console.error('Ephemeral secret key or JWT randomness not found in session storage.');
            alert('Login callback error: Session data missing. Please try logging in again.');
            window.location.href = "/"; // Or login page
            return;
        }

        sessionStorage.removeItem('zklogin_ephemeral_secret_key_b64');
        sessionStorage.removeItem('zklogin_jwt_randomness');
        
        const ephemeralKeyPair = Ed25519Keypair.fromSecretKey(fromB64(ephemeralSecretKeyB64));
        const ephemeralPublicKeySui = ephemeralKeyPair.getPublicKey().toSuiPublicKey();
        
        const { epoch } = await suiClient.getLatestSuiSystemState();
        const maxEpochForBackend = parseInt(epoch) + 2; // This should ideally be the same maxEpoch used for nonce generation

        const payload = {
            jwt: id_token,
            ephemeralPublicKey: ephemeralPublicKeySui,
            maxEpoch: maxEpochForBackend, 
            jwtRandomness: jwtRandomness,
        };

        console.log("Sending to backend for ZK proof and login:", payload);
        const response = await fetch('/api/zklogin/authenticate', { // Backend endpoint to be created
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Backend authentication successful:', result);
            alert('Login successful! Redirecting...');
            window.location.href = result.redirect_url || '/'; // Backend should specify where to redirect
        } else {
            const errorText = await response.text();
            console.error('Backend authentication failed:', response.status, errorText);
            try {
                const errorData = JSON.parse(errorText);
                alert(`Login failed: ${errorData.detail || 'Unknown error from backend.'}`);
            } catch (e) {
                alert(`Login failed: ${response.status} - ${errorText || 'Unknown error from backend.'}`);
            }
            window.location.href = "/"; // Or login page
        }

    } catch (error) {
        console.error("Error during zkLogin callback handling:", error);
        alert("Failed to complete login. Check console for details.");
        window.location.href = "/"; // Or login page
    }
}

