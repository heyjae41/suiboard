// sui-fallback.js - 최소한의 Sui 기능 구현
(function() {
  console.log("Sui 폴백 스크립트 로드됨");
  
  // 전역 sui 객체 생성
  window.sui = window.sui || {};
  
  // Ed25519Keypair 클래스
  window.sui.Ed25519Keypair = class Ed25519Keypair {
    constructor() {
      console.log("폴백 Ed25519Keypair 생성자 호출");
      this._keyData = this._generateRandomKeyData();
    }
    
    _generateRandomKeyData() {
      const privateKeyBytes = new Uint8Array(32);
      const publicKeyBytes = new Uint8Array(32);
      
      // 난수로 채우기
      for (let i = 0; i < 32; i++) {
        privateKeyBytes[i] = Math.floor(Math.random() * 256);
        publicKeyBytes[i] = Math.floor(Math.random() * 256);
      }
      
      return {
        privateKey: Array.from(privateKeyBytes),
        publicKey: Array.from(publicKeyBytes)
      };
    }
    
    getPublicKey() {
      const self = this;
      return {
        toSuiAddress() {
          // 공개키에서 주소 파생 (실제 구현과는 다름)
          const addr = Array.from(self._keyData.publicKey)
            .slice(0, 20)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
          return `0x${addr}`;
        },
        toSuiPublicKey() {
          return this.toSuiAddress();
        }
      };
    }
    
    export() {
      // base64로 인코딩된 키 반환
      return {
        privateKey: btoa(String.fromCharCode.apply(null, this._keyData.privateKey)),
        publicKey: btoa(String.fromCharCode.apply(null, this._keyData.publicKey))
      };
    }
    
    static fromSecretKey(secretKey) {
      const keypair = new window.sui.Ed25519Keypair();
      console.log("폴백 fromSecretKey 호출됨, 입력값:", secretKey);
      return keypair;
    }
  };
  
  // JsonRpcProvider 클래스
  window.sui.JsonRpcProvider = class JsonRpcProvider {
    constructor(endpoint) {
      this.endpoint = endpoint;
      console.log("폴백 JsonRpcProvider 생성:", endpoint);
    }
    
    async getLatestSuiSystemState() {
      console.log("폴백 getLatestSuiSystemState 호출");
      return { epoch: "123456" };
    }
  };
  
  // 유틸리티 함수들
  window.sui.getFullnodeUrl = function(network) {
    const networkMap = {
      'devnet': 'https://fullnode.devnet.sui.io:443',
      'testnet': 'https://fullnode.testnet.sui.io:443',
      'mainnet': 'https://fullnode.mainnet.sui.io:443'
    };
    return networkMap[network] || network;
  };
  
  window.sui.generateRandomness = function() {
    const randomBytes = new Uint8Array(32);
    for (let i = 0; i < 32; i++) {
      randomBytes[i] = Math.floor(Math.random() * 256);
    }
    return btoa(String.fromCharCode.apply(null, randomBytes));
  };
  
  window.sui.generateNonce = function(publicKey, maxEpoch, randomness) {
    const combined = `${publicKey}-${maxEpoch}-${randomness}`;
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
      hash = ((hash << 5) - hash) + combined.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash).toString();
  };
  
  window.sui.jwtToAddress = function(jwt, randomness) {
    const combined = `${jwt}-${randomness}`;
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
      hash = ((hash << 5) - hash) + combined.charCodeAt(i);
      hash |= 0;
    }
    const addr = Math.abs(hash).toString(16).padStart(40, '0');
    return `0x${addr}`;
  };
  
  window.sui.fromB64 = function(b64String) {
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
  };
  
  window.sui.toB64 = function(bytes) {
    try {
      const binary = String.fromCharCode.apply(null, bytes);
      return btoa(binary);
    } catch (e) {
      console.error("toB64 오류:", e);
      return "";
    }
  };
  
  console.log("Sui 폴백 스크립트 초기화 완료");
})(); 