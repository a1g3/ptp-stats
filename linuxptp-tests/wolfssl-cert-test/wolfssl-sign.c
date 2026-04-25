
#include <stdio.h>
#include <wolfssl/options.h>
#include <wolfssl/openssl/ssl.h>
#include <wolfssl/wolfcrypt/error-crypt.h>
#include <wolfssl/test.h>

#define PACKED __attribute__((packed))

struct ptp_header {
	uint8_t             tsmt; /* transportSpecific | messageType */
	uint8_t             ver;  /* minorVersionPTP   | versionPTP  */
	uint16_t          messageLength;
	uint8_t           domainNumber;
	uint8_t               reserved1;
	uint8_t               flagField[2];
	int64_t           correction;
	uint32_t          reserved2;
	uint16_t          sequenceId;
	uint8_t           control;
	int8_t            logMessageInterval;
} PACKED;

struct join_response_msg {
	struct ptp_header   hdr;
	uint64_t          nonce[16];
	uint64_t		    currentSeqNum;
	uint32_t			key_id;
	uint8_t             key[32];  // Ed25519 public keys are 32 bytes
	uint16_t			cert_len;
	uint8_t				cert[500];
	uint16_t			sig_len;
	uint8_t				sig[72];
	uint8_t             suffix[0];
};

int sign_buffer(const byte* buf, word32 bufLen,
                byte* sig, word32* sigLen,
                const byte* keyDer, word32 keyDerLen)
{
    int ret, idx=0;
    ecc_key key;
    WC_RNG rng;
    byte hash[SHA256_DIGEST_SIZE];

    wc_ecc_init(&key);
    wc_InitRng(&rng);

    // Load ECC private key (DER format)
    ret = wc_EccPrivateKeyDecode(keyDer, &idx, &key, keyDerLen);
    if (ret != 0) {
        printf("Failed to decode ECC private key: %d\n", ret);
        return ret;
    }
    // Hash the buffer
    ret = wc_Sha256Hash(buf, bufLen, hash);
    if (ret != 0) { 
        printf("Failed to hash buffer: %d\n", ret);
        return ret;
    }
    // Sign hash
    ret = wc_ecc_sign_hash(hash, sizeof(hash),
                           sig, sigLen,
                           &rng, &key);

    if (ret != 0) {
        printf("Failed to sign hash: %d\n", ret);
    }

    wc_ecc_free(&key);
    wc_FreeRng(&rng);

    return ret;
}

int verify_buffer(const byte* buf, word32 bufLen,
                  const byte* sig, word32 sigLen,
                  ecc_key* pubKey)
{
    int ret, idx = 0, verify = 0;
    byte hash[SHA256_DIGEST_SIZE];


    /* Hash message */
    ret = wc_Sha256Hash(buf, bufLen, hash);
    if (ret != 0) {
        printf("Failed to hash buffer: %d\n", ret);
        return ret;
    }

    /* Verify signature */
    ret = wc_ecc_verify_hash(sig, sigLen,
                             hash, sizeof(hash),
                             &verify, pubKey);

    if (ret != 0)
        return ret;

    return (verify == 1) ? 0 : -1;
}

int main() {
    int ret;
    byte sig[256];
    word32 sigLen = sizeof(sig);

    /* Example message */
    wolfCrypt_Init();

    struct join_response_msg* msg = malloc(sizeof(struct join_response_msg));
    
    srand(time(NULL));

    // 3. Fill the memory with random data
    for (int i = 0; i < sizeof(struct join_response_msg); i++) {
        ((byte*)msg)[i] = rand();
    }

    /* Load DER private key from file */
    FILE* f = fopen("alpha-key.der", "rb");
    if (!f) {
        printf("Failed to open key file\n");
        return -1;
    }

    fseek(f, 0, SEEK_END);
    long keyLen = ftell(f);
    rewind(f);

    byte* keyDer = (byte*)malloc(keyLen);
    fread(keyDer, 1, keyLen, f);
    fclose(f);

    /* Sign */
    ret = sign_buffer(
        (const byte*)msg,
        sizeof(struct join_response_msg),
        sig,
        &sigLen,
        keyDer,
        (word32)keyLen
    );

    if (ret != 0) {
        printf("Signing failed: %d\n", ret);
        free(keyDer);
        return -1;
    }

    printf("Signature (%u bytes):\n", sigLen);
    for (word32 i = 0; i < sigLen; i++)
        printf("%02X", sig[i]);
    printf("\n");

    free(keyDer);


    // Verify
    DecodedCert decodedCert;
    FILE* file;
    ecc_key eccKey;
    word32 inOutIdx = 0;

    FILE* fpub = fopen("alpha.der", "rb");
    fseek(fpub, 0, SEEK_END);
    long pubLen = ftell(fpub);
    rewind(fpub);

    byte* pubDer = malloc(pubLen);
    fread(pubDer, 1, pubLen, fpub);
    fclose(fpub);

    InitDecodedCert(&decodedCert, pubDer, (word32) pubLen, 0);

    ret = ParseCert(&decodedCert, CERT_TYPE, NO_VERIFY, NULL);
    if (ret != 0) {
        printf("Failed to parse certificate: %d\n", ret);
        free(pubDer);
        return -1;
    }
    ret = wc_ecc_init(&eccKey);
    WOLFSSL_BUFFER(decodedCert.publicKey, decodedCert.pubKeySize);

    ret = wc_EccPublicKeyDecode(decodedCert.publicKey, &inOutIdx, &eccKey, decodedCert.pubKeySize);
    if (ret != 0) {
        printf("Failed to decode ECC public key: %d\n", ret);
        free(pubDer);
        return -1;
    }

    /* Verify */
    ret = verify_buffer(
        (const byte*)msg,
        sizeof(struct join_response_msg),
        sig,
        sigLen,
        &eccKey
    );

    if (ret == 0)
        printf("Signature VALID\n");
    else
        printf("Signature INVALID\n");
        
    FreeDecodedCert(&decodedCert);
    wolfCrypt_Cleanup();

    free(pubDer);


    return 0;
}