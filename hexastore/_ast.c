#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>
// #include <object.h>
// #include <moduleobject.h>

typedef struct {
    PyObject_HEAD
    PyObject* value;
} IRIObject;

static PyTypeObject IRIType;

static void
IRI_dealloc(IRIObject *self)
{
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
IRI_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    IRIObject *self;
    self = (IRIObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->value = PyUnicode_FromString("");
        if (self->value == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *) self;
}

static int
IRI_init(IRIObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"value", NULL};
    PyObject *value = NULL, *tmp;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|U", kwlist, &value))
        return -1;

    if (value) {
        tmp = self->value;
        Py_INCREF(value);
        self->value = value;
        Py_XDECREF(tmp);
    }

    return 0;
}

static PyObject *
IRI_repr(IRIObject * obj)
{
    return PyUnicode_FromFormat(
        "IRI(value=%R)",
        obj->value
    );
}


static PyObject *
IRI_str(IRIObject * obj)
{
    Py_INCREF(obj->value);
    return obj->value;
}


static PyObject *
IRI_bytes(IRIObject *self, PyObject *Py_UNUSED(ignored))
{
    return PyUnicode_AsEncodedString(self->value, "utf-8", "strict");
}


static PyObject *
IRI_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    if(!PyObject_TypeCheck(lhs_o, &IRIType) || !PyObject_TypeCheck(rhs_o, &IRIType))
    {
        PyObject *result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    IRIObject *lhs = lhs_o;
    IRIObject *rhs = rhs_o;

    return PyObject_RichCompare(lhs->value, rhs->value, op);
}


static Py_hash_t *
IRI_hash(IRIObject *o)
{
    return PyObject_Hash(o->value);
}


static PyObject *
IRI_value(IRIObject *self, void *closure)
{
    Py_INCREF(self->value);
    return self->value;
}


static PyGetSetDef IRI_getsetters[] = {
    {"value", (getter) IRI_value, NULL, "value", NULL},
    {NULL}  /* Sentinel */
};


static PyMethodDef IRI_methods[] = {
    {"__bytes__", (PyCFunction) IRI_bytes, METH_NOARGS,
     "Return bytes representation of the IRI."
    },
    {NULL}  /* Sentinel */
};


static PyTypeObject IRIType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.IRI",
    .tp_doc = "IRI objects",
    .tp_basicsize = sizeof(IRIObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = IRI_new,
    .tp_init = (initproc) IRI_init,
    .tp_dealloc = (destructor) IRI_dealloc,
    // .tp_members = IRI_members,
    .tp_getset = IRI_getsetters,
    .tp_methods = IRI_methods,
    .tp_repr = (reprfunc) IRI_repr,
    .tp_str = (reprfunc) IRI_str,
    .tp_richcompare = IRI_richcmp,
    .tp_hash = (hashfunc) IRI_hash,
};

static PyModuleDef _hexastoremodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_hexastore",
    .m_doc = "_hexastore module",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit__hexastore(void)
{
    PyObject *m;
    if (PyType_Ready(&IRIType) < 0)
        return NULL;

    m = PyModule_Create(&_hexastoremodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&IRIType);
    if (PyModule_AddObject(m, "IRI", (PyObject *) &IRIType) < 0) {
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}