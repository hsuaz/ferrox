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
        magick_wand=DestroyMagickWand(magick_wand);
        MagickWandTerminus();
    }

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
        magick_wand=DestroyMagickWand(magick_wand);
        MagickWandTerminus();
    }

    return Py_BuildValue("(ii)", width, height);
}

static PyMethodDef ImageMagickMethods[] = {
    {"get_size",  imagemagick_get_size, METH_VARARGS, "Gets the size of an image. Returns (w,h)."},
    {"resize",  imagemagick_resize, METH_VARARGS, "Resize an image from a blob."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initimagemagick(void)
{
    (void) Py_InitModule("imagemagick", ImageMagickMethods);
}
