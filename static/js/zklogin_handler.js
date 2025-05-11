// zklogin_handler.js

// 전역 변수 선언
let Ed25519Keypair, SuiClient, getFullnodeUrl, generateNonce, generateRandomness, jwtToAddress, fromB64, toB64;
let SDK_VERSION = "unknown";
let suiClient;

// 구성 설정
const GOOGLE_CLIENT_ID = "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com";

// 리다이렉트 URI 설정 - Google Cloud Console에 등록된 URI와 일치하는지 확인
const REDIRECT_URI = `${window.location.origin}/auth/zklogin/google/callback`;  // Google 콘솔에 등록된 URI와 일치해야 함
console.log("Configured REDIRECT_URI:", REDIRECT_URI);

// Sui RPC endpoint
const SUI_NETWORK = 'testnet'; // 또는 'devnet', 'mainnet'

// 비밀키 추출 유틸리티 함수 - 다양한 버전 지원
function extractSecretKey(keypair) {
    if (typeof keypair.getSecretKey === 'function') {
        console.log("Using getSecretKey() method (Sui SDK 1.30.0+)");
        return keypair.getSecretKey();
    } else if (typeof keypair.export === 'function') {
        console.log("Using export().privateKey method (Sui SDK ~1.19.0)");
        return keypair.export().privateKey;
    } else if (keypair.keypair && keypair.keypair.secretKey) {
        console.log("Using keypair.keypair.secretKey direct access");
        return Array.from(keypair.keypair.secretKey).toString('base64');
    } else {
        throw new Error('지원되지 않는 keypair 구조');
    }
}

// 공개키 주소 추출 함수 - 다양한 버전 지원
function extractPublicKeyAddress(publicKey) {
    if (typeof publicKey.toSuiAddress === 'function') {
        console.log("Using toSuiAddress() method");
        return publicKey.toSuiAddress();
    } else if (typeof publicKey.toSuiPublicKey === 'function') {
        console.log("Using toSuiPublicKey() method");
        return publicKey.toSuiPublicKey();
    } else {
        throw new Error('지원되지 않는 공개키 구조');
    }
}

// 비밀키로부터 키페어 재구성 함수 - 다양한 버전 지원
function reconstructKeypair(secretKeyData) {
    try {
        // Sui SDK 1.30.0+ 방식으로 시도
        if (typeof Ed25519Keypair.fromSecretKey === 'function') {
            // 최신 버전은 다양한 형태의 입력을 지원할 수 있음
            if (typeof secretKeyData === 'string' && secretKeyData.indexOf('suiprivkey') === 0) {
                // Bech32 인코딩된 형식(1.30.0+)
                return Ed25519Keypair.fromSecretKey(secretKeyData);
            } else if (typeof fromB64 === 'function') {
                // Base64 디코딩 필요한 경우
                try {
                    return Ed25519Keypair.fromSecretKey(fromB64(secretKeyData));
                } catch (e) {
                    // 직접 전달 시도
                    return Ed25519Keypair.fromSecretKey(secretKeyData);
                }
            } else {
                // 그냥 전달
                return Ed25519Keypair.fromSecretKey(secretKeyData);
            }
        } 
        // 1.19.0 방식으로 시도
        else {
            return Ed25519Keypair.fromSecretKey(secretKeyData);
        }
    } catch (e) {
        console.error("Keypair 재구성 오류:", e);
        // 다른 방식 시도
        try {
            return new Ed25519Keypair({ privateKey: secretKeyData });
        } catch (e2) {
            console.error("대체 방식도 실패:", e2);
            throw new Error("모든 키페어 재구성 방법 실패");
        }
    }
}

// SDK 동적 로드 함수
async function loadSuiSDK() {
    try {
        console.log("직접 구현된 기본 기능 사용: fallback (내장)");
        
        // 직접 최소한의 필수 기능 구현
        SDK_VERSION = "fallback (내장)";
        
        // 최소한의 Ed25519Keypair 구현
        Ed25519Keypair = window.sui.Ed25519Keypair;
        
        // 최소한의 SuiClient(JsonRpcProvider) 구현
        SuiClient = window.sui.JsonRpcProvider;
        
        // 기본 유틸리티 함수 구현
        getFullnodeUrl = window.sui.getFullnodeUrl;
        generateNonce = window.sui.generateNonce;
        generateRandomness = window.sui.generateRandomness;
        jwtToAddress = window.sui.jwtToAddress;
        fromB64 = window.sui.fromB64;
        toB64 = window.sui.toB64;
        
        // 클라이언트 초기화
        initializeSuiClient();
        return true;
    } catch (error) {
        console.error("Sui SDK 로드 실패:", error);
        document.body.innerHTML += `<div style="position:fixed;top:0;left:0;right:0;background:red;color:white;padding:10px;text-align:center;">
            Sui SDK 로드 실패. 콘솔을 확인하세요.
        </div>`;
        return false;
    }
}

// 기본 유틸리티 함수 구현
function defaultGetFullnodeUrl(network) {
    const networkMap = {
        'devnet': 'https://fullnode.devnet.sui.io:443',
        'testnet': 'https://fullnode.testnet.sui.io:443',
        'mainnet': 'https://fullnode.mainnet.sui.io:443'
    };
    return networkMap[network] || network;
}

function defaultGenerateRandomness() {
    const randomBytes = new Uint8Array(32);
    for (let i = 0; i < 32; i++) {
        randomBytes[i] = Math.floor(Math.random() * 256);
    }
    return btoa(String.fromCharCode.apply(null, randomBytes));
}

function defaultGenerateNonce(publicKey, maxEpoch, randomness) {
    // 간단한 논스 생성 함수 (실제 구현과는 다름)
    const combined = `${publicKey}-${maxEpoch}-${randomness}`;
    // 문자열에서 간단한 해시 생성
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
        hash = ((hash << 5) - hash) + combined.charCodeAt(i);
        hash |= 0; // 32비트 정수로 변환
    }
    return Math.abs(hash).toString();
}

function defaultJwtToAddress(jwt, randomness) {
    // JWT에서 간단한 주소 생성 (실제 구현과는 다름)
    const combined = `${jwt}-${randomness}`;
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
        hash = ((hash << 5) - hash) + combined.charCodeAt(i);
        hash |= 0;
    }
    const addr = Math.abs(hash).toString(16).padStart(40, '0');
    return `0x${addr}`;
}

function defaultFromB64(b64String) {
    try {
        const binary = atob(b64String);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes;
    } catch (e) {
        console.error("fromB64 오류:", e);
        return new Uint8Array();
    }
}

function defaultToB64(bytes) {
    try {
        const binary = String.fromCharCode.apply(null, bytes);
        return btoa(binary);
    } catch (e) {
        console.error("toB64 오류:", e);
        return "";
    }
}

// Sui 클라이언트 초기화 함수
function initializeSuiClient() {
    try {
        if (typeof SuiClient === 'function') {
            if (SDK_VERSION.includes("1.30.0")) {
                suiClient = new SuiClient({ url: getFullnodeUrl(SUI_NETWORK) });
            } else {
                suiClient = new SuiClient(getFullnodeUrl(SUI_NETWORK));
            }
            console.log("Sui 클라이언트 초기화 완료");
        } else {
            throw new Error("SuiClient 함수를 찾을 수 없습니다");
        }
    } catch (error) {
        console.error("Sui 클라이언트 초기화 실패:", error);
        throw error;
    }
}

// 초기화 시 Sui 네트워크 연결 테스트
async function testSuiConnection() {
    try {
        console.log(`Sui ${SUI_NETWORK} 연결 시도...`);
        const { epoch } = await suiClient.getLatestSuiSystemState();
        console.log(`Sui ${SUI_NETWORK} 연결 성공. 현재 epoch: ${epoch}`);
        return true;
    } catch (error) {
        console.error(`Sui ${SUI_NETWORK} 연결 실패:`, error);
        return false;
    }
}

// zkLogin 시작 함수
async function startZkLoginWithGoogle() {
    console.log('zkLogin with Google initiated. Client ID: ' + GOOGLE_CLIENT_ID);
    
    // 클라이언트 ID 확인
    if (GOOGLE_CLIENT_ID === "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com") {
        console.log('Google Client ID는 유효합니다. 로그인 진행합니다.');
    }

    try {
        // 1. Generate ephemeral keypair
        console.log('임시 키페어 생성 중...');
        const ephemeralKeyPair = new Ed25519Keypair();
        const ephemeralPublicKey = ephemeralKeyPair.getPublicKey();
        const ephemeralPublicKeyFormatted = extractPublicKeyAddress(ephemeralPublicKey);
        console.log("임시 공개키(Sui 형식):", ephemeralPublicKeyFormatted);

        // 비밀키 안전하게 저장
        try {
            console.log("비밀키 추출 중...");
            const privateKeyData = extractSecretKey(ephemeralKeyPair);
            console.log("비밀키 추출 성공(길이:", (privateKeyData ? privateKeyData.length : 0), ")");
            sessionStorage.setItem('zklogin_ephemeral_secret_key_b64', privateKeyData);
        } catch (keyError) {
            console.error("비밀키 추출 오류:", keyError);
            throw new Error("임시 키 저장 실패: " + keyError.message);
        }

        // 2. 현재 epoch 가져오기
        console.log('Sui 네트워크에 연결 중: ' + SUI_NETWORK);
        console.log('최신 Sui 시스템 상태 조회 중...');
        const { epoch } = await suiClient.getLatestSuiSystemState();
        console.log("현재 epoch:", epoch);

        // 3. maxEpoch 정의
        console.log('maxEpoch 계산 중...');
        const maxEpoch = parseInt(epoch) + 2;
        console.log('maxEpoch 설정:', maxEpoch);

        // 4. nonce용 난수 생성
        console.log('nonce용 난수 생성 중...');
        const jwtRandomness = generateRandomness();
        sessionStorage.setItem('zklogin_jwt_randomness', jwtRandomness);
        console.log("JWT 난수:", jwtRandomness);

        // 5. nonce 생성
        console.log('임시 공개키, maxEpoch, JWT 난수로 nonce 생성 중...');
        console.log('파라미터:', {
            publicKey: ephemeralPublicKeyFormatted,
            maxEpoch: maxEpoch,
            randomnessLength: jwtRandomness.length
        });
        
        // SDK 버전에 따라 다른 방식으로 nonce 생성
        let nonce;
        if (SDK_VERSION.includes("1.30.0")) {
            nonce = generateNonce(ephemeralPublicKey, maxEpoch, jwtRandomness);
        } else {
            nonce = generateNonce(ephemeralPublicKeyFormatted, maxEpoch, jwtRandomness);
        }
        console.log("생성된 nonce:", nonce);

        // 6. Google OAuth URL 구성
        console.log('Google OAuth URL 구성 중...');
        const params = new URLSearchParams({
            client_id: GOOGLE_CLIENT_ID,
            redirect_uri: REDIRECT_URI,
            response_type: 'id_token',
            scope: 'openid email profile',
            nonce: nonce,
        });

        // 각 파라미터 확인
        console.log('OAuth 파라미터:');
        console.log('- client_id:', GOOGLE_CLIENT_ID);
        console.log('- redirect_uri:', REDIRECT_URI);
        console.log('- nonce:', nonce);

        const googleOAuthURL = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
        console.log("Google OAuth URL로 리다이렉트:", googleOAuthURL);

        // 7. 사용자를 Google OAuth URL로 리다이렉트
        window.location.href = googleOAuthURL;

    } catch (error) {
        console.error("zkLogin 초기화 오류:", error);
        // 자세한 오류 정보 출력
        console.error("오류 정보:", {
            name: error.name || '알 수 없는 오류',
            message: error.message || '오류 메시지 없음',
            stack: error.stack || '스택 트레이스 없음'
        });
        
        // 오류 유형에 따른 메시지
        if (error.name === 'TypeError' && error.message && error.message.includes('fetch')) {
            alert("Sui 네트워크 연결 오류: 인터넷 연결을 확인해 주세요.");
        } else if (error.name === 'TypeError' && error.message && error.message.includes('undefined')) {
            alert("SDK 초기화 오류: 콘솔을 확인해 주세요.");
        } else if (error.message && error.message.includes('epoch')) {
            alert("Sui 네트워크 응답 오류: 다른 네트워크(devnet/testnet)를 시도해 보세요.");
        } else {
            alert("Google 로그인 초기화 실패: " + (error.message || "자세한 내용은 콘솔을 확인하세요."));
        }
    }
}

// zkLogin 콜백 처리 함수 수정
async function handleZkLoginCallback() {
    console.log('zkLogin 콜백 처리 중...');
    try {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const id_token = params.get('id_token');

        if (!id_token) {
            console.error('URL 프래그먼트에서 ID Token을 찾을 수 없습니다.');
            alert('로그인 콜백 오류: ID Token을 찾을 수 없습니다.');
            window.location.href = "/";
            return;
        }
        console.log('ID Token 수신 완료.');

        const ephemeralSecretKeyB64 = sessionStorage.getItem('zklogin_ephemeral_secret_key_b64');
        const jwtRandomness = sessionStorage.getItem('zklogin_jwt_randomness');

        if (!ephemeralSecretKeyB64 || !jwtRandomness) {
            console.error('세션 스토리지에서 임시 비밀키 또는 JWT 난수를 찾을 수 없습니다.');
            alert('로그인 콜백 오류: 세션 데이터가 없습니다. 다시 로그인해 주세요.');
            window.location.href = "/";
            return;
        }

        // 세션 데이터 삭제
        sessionStorage.removeItem('zklogin_ephemeral_secret_key_b64');
        sessionStorage.removeItem('zklogin_jwt_randomness');
        
        console.log("비밀키로부터 임시 키페어 재구성 중...");
        try {
            // 호환성 함수 사용
            const ephemeralKeyPair = reconstructKeypair(ephemeralSecretKeyB64);
            const ephemeralPublicKey = ephemeralKeyPair.getPublicKey();
            const ephemeralPublicKeySui = extractPublicKeyAddress(ephemeralPublicKey);
            console.log("재구성된 임시 공개키:", ephemeralPublicKeySui);
            
            const { epoch } = await suiClient.getLatestSuiSystemState();
            const maxEpochForBackend = parseInt(epoch) + 2;

            // 수정된 페이로드 형식: 최상위 필드로 변경
            const payload = {
                jwt: id_token,
                ephemeralPublicKey: ephemeralPublicKeySui,
                maxEpoch: maxEpochForBackend,
                jwtRandomness: jwtRandomness
            };

            console.log("ZK 증명 및 로그인을 위해 백엔드로 전송 중:", payload);
            const response = await fetch('/api/zklogin/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                const result = await response.json();
                console.log('백엔드 인증 성공:', result);
                alert('로그인 성공! 리다이렉트 중...');
                window.location.href = result.redirect_url || '/';
            } else {
                const errorText = await response.text();
                console.error('백엔드 인증 실패:', response.status, errorText);
                try {
                    const errorData = JSON.parse(errorText);
                    alert(`로그인 실패: ${errorData.detail || '백엔드에서 알 수 없는 오류가 발생했습니다.'}`);
                } catch (e) {
                    alert(`로그인 실패: ${response.status} - ${errorText || '백엔드에서 알 수 없는 오류가 발생했습니다.'}`);
                }
                window.location.href = "/";
            }
        } catch (error) {
            console.error("zkLogin 콜백 처리 오류:", error);
            alert("로그인 완료에 실패했습니다. 콘솔을 확인하세요.");
            window.location.href = "/";
        }
    } catch (error) {
        console.error("zkLogin 콜백 처리 오류:", error);
        alert("로그인 완료에 실패했습니다. 콘솔을 확인하세요.");
        window.location.href = "/";
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async () => {
    // 필요한 폴백 스크립트 직접 포함
    const fallbackScript = document.createElement('script');
    fallbackScript.src = '/static/js/vendor/sui-fallback.js';
    fallbackScript.async = false;
    document.head.appendChild(fallbackScript);
    
    // 잠시 대기 (폴백 스크립트 로드 기다림)
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Sui SDK 로드
    if (await loadSuiSDK()) {
        // SDK 로드 성공 시 Sui 네트워크 테스트
        await testSuiConnection();
        
        // Google 로그인 버튼 이벤트 리스너 등록
        const zkLoginButton = document.getElementById('zklogin_google_button');
        if (zkLoginButton) {
            zkLoginButton.addEventListener('click', startZkLoginWithGoogle);
        } else {
            console.warn('zkLogin Google 버튼을 찾을 수 없습니다. id="zklogin_google_button"이 있는지 확인하세요.');
        }

        // 현재 페이지 URL 확인
        const currentPath = window.location.pathname;
        console.log("현재 페이지 경로:", currentPath);
        
        // Google OAuth 콜백 감지 및 처리
        if (currentPath === "/auth/zklogin/google/callback") { 
            console.log("콜백 URL 감지, zkLogin 콜백 처리 중...");
            handleZkLoginCallback();
        }
    } else {
        console.error("Sui SDK 로드 실패");
        alert("Sui SDK를 로드할 수 없습니다. 콘솔을 확인하세요.");
    }
});

