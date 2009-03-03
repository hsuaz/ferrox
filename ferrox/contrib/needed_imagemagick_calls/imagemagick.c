#include <Python.h>
#include <wand/MagickWand.h>

static PyObject *imagemagick_resize(PyObject *self, PyObject *args)
{
    const char *image_string, *new_image_string;
    int image_length, new_image_length, height, width;
    MagickBooleanType status;
    MagickWand *magick_wand;
    PyObject *output_object;

    if (!PyArg_ParseTuple(args, "s#ii", &image_string, &image_length, &width, &height))
    {
        return NULL;
    }

    MagickWandGenesis();
    magick_wand=NewMagickWand();

    status=MagickReadImageBlob(magick_wand,(const void*)image_string,image_length);
    if (status != MagickFalse)
    {
        MagickResetIterator(magick_wand);
        if (MagickNextImage(magick_wand) != MagickFalse)
        {
            MagickResizeImage(magick_wand,width,height,LanczosFilter,1.0);
        }
        new_image_string = MagickGetImageBlob(magick_wand,&new_image_length);
        output_object = PyString_FromStringAndSize(new_image_string, new_image_length);
        new_image_string = (const char *)MagickRelinquishMemory((void*)new_image_string);
    }
    magick_wand=DestroyMagickWand(magick_wand);
    MagickWandTerminus();

    return output_object;
}

static PyObject *imagemagick_get_size(PyObject *self, PyObject *args)
{
    const char *image_string;
    int image_length, height, width;
    MagickBooleanType status;
    MagickWand *magick_wand;

    if (!PyArg_ParseTuple(args, "s#", &image_string, &image_length))
    {
        return NULL;
    }

    MagickWandGenesis();
    magick_wand=NewMagickWand();

    status=MagickReadImageBlob(magick_wand,(const void*)image_string,image_length);
    if (status != MagickFalse)
    {
        MagickResetIterator(magick_wand);
        if (MagickNextImage(magick_wand) != MagickFalse)
        {
            height = MagickGetImageHeight(magick_wand);
            width = MagickGetImageWidth(magick_wand);
        }
    }
    magick_wand=DestroyMagickWand(magick_wand);
    MagickWandTerminus();

    return Py_BuildValue("(ii)", width, height);
}

static PyObject *imagemagick_get_metadata(PyObject *self, PyObject *args)
{
    const char *image_string;
    int image_length;/*, height, width;*/
    MagickBooleanType status;
    MagickWand *magick_wand;
    char** info;
    char* value;
    unsigned long numprops;
    PyObject* return_dict;
    int i;

    if (!PyArg_ParseTuple(args, "s#", &image_string, &image_length))
    {
        return NULL;
    }

    return_dict = PyDict_New();
    if ( return_dict != NULL )
    {
        Py_INCREF(return_dict);

        MagickWandGenesis();
        magick_wand=NewMagickWand();

        status=MagickReadImageBlob(magick_wand,(const void*)image_string,image_length);
        if (status != MagickFalse)
        {
            MagickResetIterator(magick_wand);
            if (MagickNextImage(magick_wand) != MagickFalse)
            {
                info = MagickGetImageProperties(magick_wand,"",&numprops);
            }
            for ( i = 0; i < (int) numprops; ++i )
            {
                value = MagickGetImageProperty(magick_wand,info[i]);
                /*printf("%45s : %s\n",info[i], value);*/
                PyDict_SetItemString(return_dict, info[i], PyString_FromString(value));
                value = (char*)MagickRelinquishMemory((void*)value);
            }
            info = (char**)MagickRelinquishMemory((void*)info);
        }
        magick_wand=DestroyMagickWand(magick_wand);
        MagickWandTerminus();
        Py_DECREF(return_dict);
    }

    return return_dict;
}


static PyMethodDef ImageMagickMethods[] = {
    {"get_size",  imagemagick_get_size, METH_VARARGS, "Gets the size of an image. Returns (w,h)."},
    {"get_metadata",  imagemagick_get_metadata, METH_VARARGS, "Gets metadata such as EXIF data. Returns dict."},
    {"resize",  imagemagick_resize, METH_VARARGS, "Resize an image from a blob."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initimagemagick(void)
{
    (void) Py_InitModule("imagemagick", ImageMagickMethods);
}
