/* Hack to hide an <object>NULL from Cython. */

#include "Python.h"

void unset_trace(void) {
    PyEval_SetTrace(NULL, NULL);
}
