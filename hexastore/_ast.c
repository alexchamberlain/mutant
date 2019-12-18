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
    .tp_flags = Py_TPFLAGS_DEFAULT,
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
    .tp_flags = Py_TPFLAGS_DEFAULT,
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
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = LangTaggedString_new,
    .tp_init = (initproc) LangTaggedString_init,
    .tp_dealloc = (destructor) LangTaggedString_dealloc,
    .tp_getset = LangTaggedString_getsetters,
    .tp_repr = (reprfunc) LangTaggedString_repr,
    .tp_str = (reprfunc) LangTaggedString_str,
    .tp_richcompare = LangTaggedString_richcmp,
    .tp_hash = (hashfunc) LangTaggedString_hash,
};

typedef struct {
    PyObject_HEAD
    PyObject* value;
    PyObject* datatype;
} TypedLiteralObject;

static PyTypeObject TypedLiteralType;

static void
TypedLiteral_dealloc(TypedLiteralObject *self)
{
    Py_XDECREF(self->datatype);
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
IRI_FromString(const char *in)
{
    IRIObject *self;
    self = (IRIObject *) IRIType.tp_alloc(&IRIType, 0);
    if (self != NULL) {
        self->value = PyUnicode_FromString(in);
        if (self->value == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *) self;
}

static PyObject *
TypedLiteral_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    TypedLiteralObject *self;
    self = (TypedLiteralObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->value = PyUnicode_FromString("");
        if (self->value == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        
        self->datatype = IRI_FromString("");
        if (self->datatype == NULL) {
            Py_DECREF(self->value);
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *) self;
}

static int
TypedLiteral_init(TypedLiteralObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"value", "datatype", NULL};
    PyObject *value = NULL, *datatype = NULL, *tmp;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|UO", kwlist, &value, &datatype))
    {
        return -1;
    }

    if (value) {
        tmp = self->value;
        Py_INCREF(value);
        self->value = value;
        Py_XDECREF(tmp);
    }

    if (datatype) {
        if (!PyObject_TypeCheck(datatype, &IRIType)) {
            PyErr_SetString(PyExc_TypeError,
                            "argument 2 must be _hexastore.IRI, not str");
            return -1;
        }

        tmp = self->datatype;
        Py_INCREF(datatype);
        self->datatype = datatype;
        Py_XDECREF(tmp);
    }

    return 0;
}

static PyObject *
TypedLiteral_repr(TypedLiteralObject * obj)
{
    return PyUnicode_FromFormat(
        "TypedLiteral(value=%R, datatype=%R)",
        obj->value,
        obj->datatype
    );
}


static PyObject *
TypedLiteral_str(TypedLiteralObject * obj)
{
    return PyUnicode_FromFormat(
        "%R^^%R",
        obj->value,
        obj->datatype
    );
}


static PyObject *
TypedLiteral_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    if(!PyObject_TypeCheck(lhs_o, &TypedLiteralType) || !PyObject_TypeCheck(rhs_o, &TypedLiteralType))
    {
        PyObject *result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    TypedLiteralObject *lhs = lhs_o;
    TypedLiteralObject *rhs = rhs_o;

    int r = PyObject_RichCompareBool(lhs->value, rhs->value, Py_EQ);

    switch(r) {
        case 1:
            return PyObject_RichCompare(lhs->datatype, rhs->datatype, op);
        case 0:
            return PyObject_RichCompare(lhs->value, rhs->value, op);
        default:
            return NULL;
    }
}


static Py_hash_t *
TypedLiteral_hash(TypedLiteralObject *o)
{
    // TODO: I have no idea if this is any good
    return PyObject_Hash(o->value) * 0x093e0562 + PyObject_Hash(o->datatype);
}


static PyObject *
TypedLiteral_value(TypedLiteralObject *self, void *closure)
{
    Py_INCREF(self->value);
    return self->value;
}


static PyObject *
TypedLiteral_datatype(TypedLiteralObject *self, void *closure)
{
    Py_INCREF(self->datatype);
    return self->datatype;
}

static PyGetSetDef TypedLiteral_getsetters[] = {
    {"value", (getter) TypedLiteral_value, NULL, "value", NULL},
    {"datatype", (getter) TypedLiteral_datatype, NULL, "datatype", NULL},
    {NULL}  /* Sentinel */
};


static PyTypeObject TypedLiteralType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.TypedLiteral",
    .tp_doc = "TypedLiteral objects",
    .tp_basicsize = sizeof(TypedLiteralObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = TypedLiteral_new,
    .tp_init = (initproc) TypedLiteral_init,
    .tp_dealloc = (destructor) TypedLiteral_dealloc,
    .tp_getset = TypedLiteral_getsetters,
    .tp_repr = (reprfunc) TypedLiteral_repr,
    .tp_str = (reprfunc) TypedLiteral_str,
    .tp_richcompare = TypedLiteral_richcmp,
    .tp_hash = (hashfunc) TypedLiteral_hash,
};




typedef struct {
    PyObject_HEAD
    PyObject* value;
} VariableObject;

static PyTypeObject VariableType;

static void
Variable_dealloc(VariableObject *self)
{
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
Variable_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    VariableObject *self;
    self = (VariableObject *) type->tp_alloc(type, 0);
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
Variable_init(VariableObject *self, PyObject *args, PyObject *kwds)
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
Variable_repr(VariableObject * obj)
{
    return PyUnicode_FromFormat(
        "Variable(value=%R)",
        obj->value
    );
}


static PyObject *
Variable_str(VariableObject * obj)
{
    Py_INCREF(obj->value);
    return obj->value;
}


static PyObject *
Variable_bytes(VariableObject *self, PyObject *Py_UNUSED(ignored))
{
    return PyUnicode_AsEncodedString(self->value, "utf-8", "strict");
}


static PyObject *
Variable_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    if(!PyObject_TypeCheck(lhs_o, &VariableType) || !PyObject_TypeCheck(rhs_o, &VariableType))
    {
        PyObject *result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    VariableObject *lhs = lhs_o;
    VariableObject *rhs = rhs_o;

    return PyObject_RichCompare(lhs->value, rhs->value, op);
}


static Py_hash_t *
Variable_hash(VariableObject *o)
{
    return PyObject_Hash(o->value);
}


static PyObject *
Variable_value(VariableObject *self, void *closure)
{
    Py_INCREF(self->value);
    return self->value;
}


static PyGetSetDef Variable_getsetters[] = {
    {"value", (getter) Variable_value, NULL, "value", NULL},
    {NULL}  /* Sentinel */
};


static PyMethodDef Variable_methods[] = {
    {"__bytes__", (PyCFunction) Variable_bytes, METH_NOARGS,
     "Return bytes representation of the Variable."
    },
    {NULL}  /* Sentinel */
};


static PyTypeObject VariableType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.Variable",
    .tp_doc = "Variable objects",
    .tp_basicsize = sizeof(VariableObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Variable_new,
    .tp_init = (initproc) Variable_init,
    .tp_dealloc = (destructor) Variable_dealloc,
    .tp_getset = Variable_getsetters,
    .tp_methods = Variable_methods,
    .tp_repr = (reprfunc) Variable_repr,
    .tp_str = (reprfunc) Variable_str,
    .tp_richcompare = Variable_richcmp,
    .tp_hash = (hashfunc) Variable_hash,
};


typedef struct {
    PyObject_HEAD
    PyObject* value;
} KeyObject;

static PyTypeObject KeyType;
static PyObject *KeyTypeOrder;

static void
Key_dealloc(KeyObject *self)
{
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static int
Key_init(KeyObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"value", NULL};
    PyObject *value = NULL, *tmp;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &value))
        return -1;

    if (value) {
        PyObject* type = Py_TYPE(value);
        PyObject* entry = PyDict_GetItem(KeyTypeOrder, type);

        if(entry == NULL)
        {
            PyErr_SetString(
                PyExc_TypeError,
                "argument 1 must be a valid RDF term"
            );
            return -1;
        }

        tmp = self->value;
        Py_INCREF(value);
        self->value = value;
        Py_XDECREF(tmp);
    }

    return 0;
}

static PyObject *
Key_repr(KeyObject * obj)
{
    return PyUnicode_FromFormat(
        "Key(value=%R)",
        obj->value
    );
}


static PyObject *
Key_richcmp(PyObject *lhs_o, PyObject *rhs_o, int op)
{
    if(!PyObject_TypeCheck(lhs_o, &KeyType) || !PyObject_TypeCheck(rhs_o, &KeyType))
    {
        PyObject *result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }

    KeyObject *lhs = lhs_o;
    KeyObject *rhs = rhs_o;

    PyObject *lhs_value = lhs->value;
    PyObject *rhs_value = rhs->value;

    if(lhs_value == rhs_value)
    {
        switch (op) {
            case Py_LT:
            case Py_NE:
            case Py_GT:
                Py_INCREF(Py_False);
                return Py_False;
            case Py_LE:
            case Py_EQ:
            case Py_GE:
                Py_INCREF(Py_True);
                return Py_True;
            default:
                Py_UNREACHABLE();
        }
    }

    if (lhs_value == NULL) {
        // TODO: What is the right exception type here?
        PyErr_SetString(PyExc_AttributeError, "lhs->value is NULL");
        return NULL;
    }

    if (rhs_value == NULL) {
        PyErr_SetString(PyExc_AttributeError, "rhs->value is NULL");
        return NULL;
    }

    PyTypeObject *lhs_type = Py_TYPE(lhs_value);
    PyTypeObject *rhs_type = Py_TYPE(rhs_value);

    if(lhs_type != rhs_type)
    {
        switch (op) {
            case Py_NE:
                Py_INCREF(Py_True);
                return Py_True;
            case Py_EQ:
                Py_INCREF(Py_False);
                return Py_False;
        }

        PyObject* lhs_entry = PyDict_GetItem(KeyTypeOrder, lhs_type);
        PyObject* rhs_entry = PyDict_GetItem(KeyTypeOrder, rhs_type);

        if (lhs_entry == NULL) {
            PyErr_SetString(PyExc_AttributeError, "lhs_entry is NULL");
            return NULL;
        }

        if (rhs_entry == NULL) {
            PyErr_SetString(PyExc_AttributeError, "rhs_entry is NULL");
            return NULL;
        }

        // TODO: Handle interspersing TypedLiteral among other types.
        long lhs_order = PyLong_AsLong(lhs_entry);
        long rhs_order = PyLong_AsLong(rhs_entry);

        int r;

        switch (op) {
            case Py_LT:
            case Py_LE:
                r = lhs_order < rhs_order;
                break;
            case Py_GT:
            case Py_GE:
                r = lhs_order > rhs_order;
                break;
        }

        PyObject *result = r ? Py_True : Py_False;
        Py_INCREF(result);
        return result;
    }

    if(lhs_type == &PyTuple_Type)
    {
        if(PyTuple_Size(lhs_value) != 3 || PyTuple_Size(rhs_value) != 3)
        {
            PyObject *result = Py_NotImplemented;
            Py_INCREF(result);
            return result;
        }

        for(size_t i = 0; i < 3; ++i)
        {
            PyObject *lhs_item = PyTuple_GET_ITEM(lhs_value, i);
            PyObject *rhs_item = PyTuple_GET_ITEM(rhs_value, i);

            int r = PyObject_RichCompareBool(lhs_item, rhs_item, Py_EQ);

            switch(r) {
                case 1:
                    continue;
                case 0:
                    return PyObject_RichCompare(lhs_item, rhs_item, op);
                default:
                    return NULL;
            }
        }

        switch (op) {
            case Py_LT:
            case Py_NE:
            case Py_GT:
                Py_INCREF(Py_False);
                return Py_False;
            case Py_LE:
            case Py_EQ:
            case Py_GE:
                Py_INCREF(Py_True);
                return Py_True;
            default:
                Py_UNREACHABLE();
        }
    }

    return PyObject_RichCompare(lhs->value, rhs->value, op);
}


static PyObject *
Key_value(KeyObject *self, void *closure)
{
    Py_INCREF(self->value);
    return self->value;
}


static PyGetSetDef Key_getsetters[] = {
    {"value", (getter) Key_value, NULL, "value", NULL},
    {NULL}  /* Sentinel */
};


static PyTypeObject KeyType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_hexastore.Key",
    .tp_doc = "Key objects",
    .tp_basicsize = sizeof(KeyObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc) Key_init,
    .tp_dealloc = (destructor) Key_dealloc,
    .tp_getset = Key_getsetters,
    .tp_repr = (reprfunc) Key_repr,
    .tp_richcompare = Key_richcmp,
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

    if (PyType_Ready(&TypedLiteralType) < 0)
        return NULL;

    if (PyType_Ready(&VariableType) < 0)
        return NULL;

    if (PyType_Ready(&KeyType) < 0)
        return NULL;

    PyObject* decimal = PyImport_ImportModuleNoBlock("decimal");
    if (decimal == NULL){
        return NULL;
    }
    PyObject* DecimalType = PyObject_GetAttrString(decimal, "Decimal");
    Py_DECREF(decimal);

    KeyTypeOrder = PyDict_New();

    if(KeyTypeOrder == NULL) {
        return NULL;
    }

    PyDict_SetItem(KeyTypeOrder, (PyObject*) Py_TYPE(Py_None), PyLong_FromLong(0));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &PyTuple_Type, PyLong_FromLong(1));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &BlankNodeType, PyLong_FromLong(2));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &IRIType, PyLong_FromLong(3));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &PyUnicode_Type, PyLong_FromLong(4));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &LangTaggedStringType, PyLong_FromLong(5));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &PyLong_Type, PyLong_FromLong(6));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) DecimalType, PyLong_FromLong(7));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &PyFloat_Type, PyLong_FromLong(8));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &TypedLiteralType, PyLong_FromLong(9));
    PyDict_SetItem(KeyTypeOrder, (PyObject*) &VariableType, PyLong_FromLong(10));

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

    Py_INCREF(&TypedLiteralType);
    if (PyModule_AddObject(m, "TypedLiteral", (PyObject *) &TypedLiteralType) < 0) {
        Py_DECREF(&TypedLiteralType);
        Py_DECREF(&LangTaggedStringType);
        Py_DECREF(&BlankNodeType);
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }

    Py_INCREF(&VariableType);
    if (PyModule_AddObject(m, "Variable", (PyObject *) &VariableType) < 0) {
        Py_DECREF(&VariableType);
        Py_DECREF(&TypedLiteralType);
        Py_DECREF(&LangTaggedStringType);
        Py_DECREF(&BlankNodeType);
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }

    Py_INCREF(&KeyType);
    if (PyModule_AddObject(m, "Key", (PyObject *) &KeyType) < 0) {
        Py_DECREF(&KeyType);
        Py_DECREF(&VariableType);
        Py_DECREF(&TypedLiteralType);
        Py_DECREF(&LangTaggedStringType);
        Py_DECREF(&BlankNodeType);
        Py_DECREF(&IRIType);
        Py_DECREF(m);
        return NULL;
    }


    return m;
}