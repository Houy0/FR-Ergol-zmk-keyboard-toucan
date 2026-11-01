/*
 * SPDX-License-Identifier: MIT
 * Defaults adapted from OneDeadKey/zmk-config-aekeynox, revision
 * 3cadeede766f31bc1e34d7c9d8ee918073cf8478, include/aekeynox/defaults.h.
 * Copyright (c) 2024 The ZMK Contributors
 */

#ifndef TOUCAN_SELENIUM_TIMING_H
#define TOUCAN_SELENIUM_TIMING_H

/* Independent hold-tap decision thresholds, in milliseconds. */
#ifndef TAP_PREFERRED_MS
#define TAP_PREFERRED_MS 300
#endif

#ifndef HOLD_PREFERRED_MS
#define HOLD_PREFERRED_MS 150
#endif

/* Tap, then hold the same key inside this window to repeat its tap action. */
#ifndef QUICK_TAP_MS
#define QUICK_TAP_MS 200
#endif

/* Lifetime of a pending one-shot; independent of hold-tap thresholds. */
#ifndef STICKY_TIMEOUT_MS
#define STICKY_TIMEOUT_MS 1000
#endif

#endif /* TOUCAN_SELENIUM_TIMING_H */
