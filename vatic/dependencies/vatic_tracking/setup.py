from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

source = [
    "cpptrack/cpptrack.pyx",
    "cpptrack/trackingmodule.cpp",
    "cpptrack/CompressiveTracker.cpp",
    "cpptrack/CompressiveTrackerModule.cpp",
    "cpptrack/BidirectionTrackerModule.cpp",
    "cpptrack/RandomFullTracker.cpp",
    # TLD
    "cpptrack/TldTrackerModule.cpp",
    "cpptrack/TldTracker.cpp",
    "cpptrack/TLD.cpp",
    "cpptrack/tld_utils.cpp",
    "cpptrack/LKTracker.cpp",
    "cpptrack/FerNNClassifier.cpp",
    # BiTLD
    "cpptrack/BiTldTrackerModule.cpp",
]

#    extra_link_args=['-fpermissive'],
#    extra_compile_args=['-fpermissive', '-std=c++11'],
# the extension here needs to be pointing to the correct version of opencv
extensions = Extension(
    "cpptrack",
    sources=source,
    include_dirs = ['/opt/opencv-2.4.12/include'],
    library_dirs = ['/opt/opencv-2.4.12/lib'],
    libraries=["opencv_highgui", "opencv_core", "opencv_imgproc","opencv_legacy"],
    language="c++",
)

setup(
    name = "tracking",
    author = "John Doherty, Charlie Ma",
    packages = ["tracking", "pytrack"],
    ext_modules = cythonize(extensions),
    data_files=[('config', ['./cpptrack/TLDparameters.yml'])]
)
