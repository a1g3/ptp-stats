/* certverify.c
 *
 * Copyright (C) 2006-2018 wolfSSL Inc.
 *
 * This file is part of wolfSSL.
 *
 * wolfSSL is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * wolfSSL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA
 */

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

    wolfSSL_Init();
    wolfSSL_Debugging_ON();

    cm = wolfSSL_CertManagerNew();
    if (cm == NULL) {
        printf("wolfSSL_CertManagerNew() failed\n");
        return -1;
    }

    //wolfSSL_CertManagerSetVerify(cm, clockVerify);

    printf("Loading CA certificate from %s\n", caCert);
    ret = wolfSSL_CertManagerLoadCA(cm, caCert, NULL);
    if (ret != WOLFSSL_SUCCESS) {
        printf("wolfSSL_CertManagerLoadCA() failed (%d): %s\n",
                ret, wolfSSL_ERR_reason_error_string(ret));
        return -1;
    }

    ret = wolfSSL_CertManagerVerifyBuffer(cm, buffer, length, SSL_FILETYPE_PEM);
    if (ret != WOLFSSL_SUCCESS) {
        printf("wolfSSL_CertManagerVerify() failed (%d): %s\n",
                ret, wolfSSL_ERR_reason_error_string(ret));
        return -1;
    }
    printf("Verification Successful!\n");

    wolfSSL_CertManagerFree(cm);
    wolfSSL_Cleanup();

    return ret;
}