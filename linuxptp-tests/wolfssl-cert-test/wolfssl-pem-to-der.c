#include <stdio.h>
#include <wolfssl/options.h>
#include <wolfssl/openssl/ssl.h>
#include <wolfssl/wolfcrypt/error-crypt.h>
#include <wolfssl/test.h>

int main(void)
{
    int ret;
    WOLFSSL_CERT_MANAGER* cm = NULL;

    const char* caCert     = "ca.pem";
    const char* verifyCert = "alpha.crt";

    char* buffer = NULL;
    FILE* f = fopen(verifyCert, "rb"); // Open in binary mode for consistent results
    int length = 0;
    char derBuffer[500]; // Buffer for DER output
    int derLength = 0;

    if (f) {
        fseek(f, 0, SEEK_END); // Seek to the end of the file
        length = ftell(f);    // Get the file size (offset from the beginning)
        rewind(f);             // Go back to the start of the file

        // Allocate memory for the entire content plus a null terminator
        buffer = (char*)malloc(length * sizeof(char));
        if (buffer) {
            // Read the file into the buffer
            fread(buffer, sizeof(char), length, f);
        }
        fclose(f); // Close the file
    }

    derLength = wc_CertPemToDer(buffer, length, derBuffer, 500, 0); // Get the DER length
    printf("PEM length: %d\n", length);
    printf("DER length: %d\n", derLength);

    return 0;
}