/*
 * SPDX-License-Identifier: MIT
 * Adapted from OneDeadKey/zmk-config-aekeynox, revision
 * 3cadeede766f31bc1e34d7c9d8ee918073cf8478:
 * include/aekeynox/aliases/ergol.h and aliases.h.
 * Copyright (c) 2024 The ZMK Contributors
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#ifndef TOUCAN_SELENIUM_ERGOL_H
#define TOUCAN_SELENIUM_ERGOL_H

#include <dt-bindings/zmk/keys.h>

/* Native Ergo-L must be selected on the Windows host. These are HID usages,
 * not the names of the resulting characters. In particular, Copy uses W.
 */
#define X_UNDO  &kp LC(Z)
#define X_CUT   &kp LC(X)
#define X_COPY  &kp LC(W)
#define X_PASTE &kp LC(V)
#define X_REDO  &kp LC(P)
#define X_CTL_W &kp LC(T)
#define X_SAVE  &kp LC(S)
#define X_ALL   &kp LC(A)
#define X_SHTAB &kp RS(TAB)

/* Symbols, row 1: ^ < > $ % | @ & * ' ` */
#define S_CARET &kp CARET
#define S_LT    &kp NUBS
#define S_GT    &kp PIPE2
#define S_DLLR  &kp DLLR
#define S_PRCNT &kp PRCNT
#define S_AT    &kp RPAR
#define S_AMPS  &kp AMPS
#define S_STAR  &kp STAR
#define S_SQT   &kp SQT
#define S_GRAVE &kp GRAVE

/* Symbols, row 2: { ( ) } = | \ + - / " */
#define S_LBRC  &kp LBRC
#define S_LPAR  &kp RA(S)
#define S_RPAR  &kp RA(D)
#define S_RBRC  &kp RBRC
#define S_EQUAL &kp EQUAL
#define S_BSLH  &kp BSLH
#define S_PLUS  &kp PLUS
#define S_MINUS &kp C
#define S_FSLH  &kp MINUS
#define S_DQT   &kp DQT

/* Symbols, row 3: ~ [ ] _ # | | ! ; : ? */
#define S_TILDE &kp TILDE
#define S_LBKT  &kp LBKT
#define S_RBKT  &kp RBKT
#define S_UNDER &kp UNDER
#define S_HASH  &kp LPAR
#define S_PIPE  &kp PIPE
#define S_EXCL  &kp RS(O)
#define S_SEMI  &kp LS(DOT)
#define S_COLON &kp LS(N)
#define S_QMARK &kp LS(C)

/* Date/number punctuation and unshifted native Ergo-L digits. */
#define S_COMMA &kp DOT
#define S_DOT   &kp N
#define S_N0    &kp N0
#define S_N1    &kp N1
#define S_N2    &kp N2
#define S_N3    &kp N3
#define S_N4    &kp N4
#define S_N5    &kp N5
#define S_N6    &kp N6
#define S_N7    &kp N7
#define S_N8    &kp N8
#define S_N9    &kp N9

#endif /* TOUCAN_SELENIUM_ERGOL_H */
