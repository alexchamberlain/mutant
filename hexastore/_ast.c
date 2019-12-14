#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>


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
    .tp_getset = IRI_getsetters,
    .tp_methods = IRI_methods,
    .tp_repr = (reprfunc) IRI_repr,
    .tp_str = (reprfunc) IRI_str,
    .tp_richcompare = IRI_richcmp,
    .tp_hash = (hashfunc) IRI_hash,
};




typedef struct {
    PyObject_HEAD
    PyObject* factory;
    unsigned long long id;
} BlankNodeObject;

static PyTypeObject BlankNodeType;

static void
BlankNode_dealloc(BlankNodeObject *self)
{
    Py_XDECREF(self->factory);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
BlankNode_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    BlankNodeObject *self;
    self = (BlankNodeObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->factory = PyUnicode_FromString("");
        if (self->factory == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->id = 0;
    }
    return (PyObject *) self;
}

static int
BlankNode_init(BlankNodeObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"id", "factory", NULL};
    unsigned long long id = 0;
    PyObject *factory = NULL, *tmp;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|KO", kwlist, &id, &factory))
    {
        return -1;
    }

    self->id = id;

    if (factory) {
        tmp = self->factory;
        Py_INCREF(factory);
        self->factory = factory;
        Py_XDECREF(tmp);
    }

    return 0;
}

static PyObject *
BlankNode_str_repr(BlankNodeObject * obj)
{
    return PyUnicode_FromFormat(
        "BlankNode(id=%llu, factory=%R)",
        obj->id,
        obj->factory
    );
}


static PyObject *
BlankNode_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    PyObject *result;
    int c;

    if(!PyObject_TypeCheck(lhs_o, &BlankNodeType) || !PyObject_TypeCheck(rhs_o, &BlankNodeType))
    {
        result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    BlankNodeObject *lhs = lhs_o;
    BlankNodeObject *rhs = rhs_o;

    if(lhs->factory != rhs->factory)
    {
        result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
    
    switch (op) {
        case Py_LT: c = lhs->id < rhs->id; break;
        case Py_LE: c = lhs->id <= rhs->id; break;
        case Py_EQ: c = lhs->id == rhs->id; break;
        case Py_NE: c = lhs->id != rhs->id; break;
        case Py_GT: c = lhs->id > rhs->id; break;
        case Py_GE: c = lhs->id >= rhs->id; break;
    }

    result = c ? Py_True : Py_False;
    Py_INCREF(result);
    return result;
}


static Py_hash_t *
BlankNode_hash(BlankNodeObject *o)
{
    PyObject *id_o = PyLong_FromUnsignedLong(o->id);

    // TODO: I have no idea if this is any good.
    return PyObject_Hash(o->factory) * 0x1571b178 + PyObject_Hash(id_o);
}


static PyTypeObject BlankNodeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.BlankNode",
    .tp_doc = "BlankNode objects",
    .tp_basicsize = sizeof(IRIObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = BlankNode_new,
    .tp_init = (initproc) BlankNode_init,
    .tp_dealloc = (destructor) BlankNode_dealloc,
    .tp_repr = (reprfunc) BlankNode_str_repr,
    .tp_str = (reprfunc) BlankNode_str_repr,
    .tp_richcompare = BlankNode_richcmp,
    .tp_hash = (hashfunc) BlankNode_hash,
};

typedef struct {
    PyObject_HEAD
    PyObject* value;
    PyObject* language;
} LangTaggedStringObject;

static PyTypeObject LangTaggedStringType;

static void
LangTaggedString_dealloc(LangTaggedStringObject *self)
{
    Py_XDECREF(self->language);
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
LangTaggedString_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    LangTaggedStringObject *self;
    self = (LangTaggedStringObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->value = PyUnicode_FromString("");
        if (self->value == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        
        self->language = PyUnicode_FromString("");
        if (self->language == NULL) {
            Py_DECREF(self->value);
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *) self;
}

static int
LangTaggedString_init(LangTaggedStringObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"value", "language", NULL};
    PyObject *value = NULL, *language = NULL, *tmp;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|UU", kwlist, &value, &language))
    {
        return -1;
    }

    if (value) {
        tmp = self->value;
        Py_INCREF(value);
        self->value = value;
        Py_XDECREF(tmp);
    }

    if (language) {
        tmp = self->language;
        Py_INCREF(language);
        self->language = language;
        Py_XDECREF(tmp);
    }

    return 0;
}

static PyObject *
LangTaggedString_repr(LangTaggedStringObject * obj)
{
    return PyUnicode_FromFormat(
        "LangTaggedString(value=%R, language=%R)",
        obj->value,
        obj->language
    );
}


static PyObject *
LangTaggedString_str(LangTaggedStringObject * obj)
{
    return PyUnicode_FromFormat(
        "%R@%U",
        obj->value,
        obj->language
    );
}


static PyObject *
LangTaggedString_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    if(!PyObject_TypeCheck(lhs_o, &LangTaggedStringType) || !PyObject_TypeCheck(rhs_o, &LangTaggedStringType))
    {
        PyObject *result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    LangTaggedStringObject *lhs = lhs_o;
    LangTaggedStringObject *rhs = rhs_o;

    int r = PyObject_RichCompareBool(lhs->value, rhs->value, Py_EQ);

    switch(r) {
        case 1:
            return PyObject_RichCompare(lhs->language, rhs->language, op);
        case 0:
            return PyObject_RichCompare(lhs->value, rhs->value, op);
        default:
            return NULL;
    }
}


static Py_hash_t *
LangTaggedString_hash(LangTaggedStringObject *o)
{
    // TODO: I have no idea if this is any good
    return PyObject_Hash(o->value) * 0x093e0562 + PyObject_Hash(o->language);
}


static PyObject *
LangTaggedString_value(LangTaggedStringObject *self, void *closure)
{
    Py_INCREF(self->value);
    return self->value;
}


static PyObject *
LangTaggedString_language(LangTaggedStringObject *self, void *closure)
{
    Py_INCREF(self->language);
    return self->language;
}

static PyGetSetDef LangTaggedString_getsetters[] = {
    {"value", (getter) LangTaggedString_value, NULL, "value", NULL},
    {"language", (getter) LangTaggedString_language, NULL, "language", NULL},
    {NULL}  /* Sentinel */
};


static PyTypeObject LangTaggedStringType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.LangTaggedString",
    .tp_doc = "LangTaggedString objects",
    .tp_basicsize = sizeof(LangTaggedStringObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = LangTaggedString_new,
    .tp_init = (initproc) LangTaggedString_init,
    .tp_dealloc = (destructor) LangTaggedString_dealloc,
    .tp_getset = LangTaggedString_getsetters,
    .tp_repr = (reprfunc) LangTaggedString_repr,
    .tp_str = (reprfunc) LangTaggedString_str,
    .tp_richcompare = LangTaggedString_richcmp,
    .tp_hash = (hashfunc) LangTaggedString_hash,
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

    if (PyType_Ready(&BlankNodeType) < 0)
        return NULL;

    if (PyType_Ready(&LangTaggedStringType) < 0)
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

    Py_INCREF(&BlankNodeType);
    if (PyModule_AddObject(m, "BlankNode", (PyObject *) &BlankNodeType) < 0) {
        Py_DECREF(&BlankNodeType);
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }

    Py_INCREF(&LangTaggedStringType);
    if (PyModule_AddObject(m, "LangTaggedString", (PyObject *) &LangTaggedStringType) < 0) {
        Py_DECREF(&LangTaggedStringType);
        Py_DECREF(&BlankNodeType);
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}