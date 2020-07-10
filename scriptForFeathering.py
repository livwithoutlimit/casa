"""
This script allows you to feather high- and low-resolution 
(i.e. interferometric and single-dish) data,
specifically those observed with ALMA.

This script is not intended to be executed in its entirety.
Rather, you should copy lines into CASA and make adjustments as necessary.

Commands should be executed in the directory where you would like the 
final feathered images to be stored. Intermediate files will be stored
in this directory as well. 

Script compiled by O. H. Wilkins with the help of S. Wood and M. Hoffman.

Lines beginning with "ACHTUNG!" after the INPUTS section warn you that data-specific information is needed at these lines.

"""

####################
###### INPUTS ######
####################

# Enter the naming conventions you'd like to use 
# to keep track of your data sets and for file names.
# TP = Total Power (or low-resolution data)
# 7m = ACA (or high-resolution data)

SourceName = '' # Name of source e.g. BGPS4449, Orion_KL
BandName = '' # Name of band; useful for observations with multiple LO settings e.g. lower, Band6
SourceBand = SourceName+'_'+BandName
spwTP = '' # Name for the low-resolution / single-dish data; indicate if feathering images for multiple spectral windows e.g. spw17_TP
spw7m = '' # Name for the high-resolution / interferometric data; indicate if feathering images for multiple spectral windows e.g. spw16_7m

# Enter the path to the FITS image for the low-resolution data
# you'd like to import for feathering.
TPfits = '' # Enter the path of the low-resolution / single-dish *.FITS file.
ACAimage = '' # Enter the path of the high-resolution / interferometric CASA *.image file.

# Enter the path for the CASA primary beam file for the high-resolution 
# data you'd like to feather. 
ACApb = '' # This is a *.pb file.


# These lines automatically generate your
# file naming conventions from above. 
ParentTP = SourceBand+'.'+spwTP
Parent7m = SourceBand+'.'+spw7m

####################
## PREPARE IMAGES ##
####################

# Copy relevant files to the feathering directory. (Do not change!)
importfits(fitsimage=TPfits,
imagename=ParentTP+'.image')
os.system('cp -rf '+ACAimage+' '+Parent7m+'.image')
os.system('cp -rf '+ACApb+' '+Parent7m+'.pb')


# Check rest frequency values of both images
imhead(ParentTP+'.image',mode='get',hdkey='restfreq')
imhead(Parent7m+'.image',mode='get',hdkey='restfreq') 

# ACHTUNG! Data-specific information required! 
# If rest frequency values are not the same, use 'imreframe' 
# command to set TP rest frequency to that of the 7m array:
imreframe(imagename=ParentTP+'.image',restfreq='241843649999.99997Hz') # Replace 241843649999.99997Hz with the rest frequency of the high-resolution / interferometric data.


# Regrid TP image to match 7m image. (Do not change!)
os.system('rm -rf '+ParentTP+'.regrid')
imregrid(imagename=ParentTP+'.image',
         template=Parent7m+'.pb',
         axes=[0, 1, 2, 3],
         output=ParentTP+'.regrid')


# ImSubImage everything (TP and PB for sure, as well as 7m for completeness).
# First, open the high-resolution image in the CASA viewer to see what image
# size you need. 
viewer(Parent7m+'.image')

# ACHTUNG! Data-specific information required!
# Specify the 'box' dimensions for your image by identifying
# lower left and upper right pixel bounds.
# FORMAT: Box = 'lower left x, lower left y, upper right x, upper right y'
Box = '' # e.g. Box = '30,30,315,330'

# Run imsubimage on everything.
imsubimage(imagename=ParentTP+'.regrid', outfile=ParentTP+'.regrid.subimage', box=Box)
imsubimage(imagename=Parent7m+'.image', box=Box,outfile=Parent7m+'.image.subimage')
imsubimage(imagename=Parent7m+'.pb',box=Box, outfile=Parent7m+'.pb.subimage')

# Check the ctypes. Often ctypes 3 and 4 (Frequency and Stokes) are switched. 
imhead(ParentTP+'.regrid.subimage',mode='list')
imhead(Parent7m+'.pb.subimage',mode='list')

# If the ctypes are out of order, reorder them. Otherwise, skip this step.
imtrans(imagename=ParentTP+'.regrid.subimage',
        outfile=ParentTP+'.regrid.subimage.ro', # ro = reorder
	order='0132')


# Multiply TP image by the 7m beam response. (Do not change!)
immath(imagename=[ParentTP+'.regrid.subimage.ro',Parent7m+'.pb.subimage'],
       mode='evalexpr',
       expr='IM0*IM1',
       outfile=ParentTP+'.regrid.subimage.ro.depb')


####################
##### FEATHER  #####
####################

# Feather the images. (Do not change!)
os.system('rm -rf '+SourceBand+'.feather_'+spw7m+'_and_'+spwTP+'.image')
feather(imagename=SourceBand+'.feather_'+spw7m+'_and_'+spwTP+'.image',
        highres=Parent7m+'.image.subimage',
        lowres=ParentTP+'.regrid.subimage.ro.depb')


####################
## PB CORRECTION ###
####################

# Generate a primary-beam-corrected (pbcor) image. (Do not change!)
immath(imagename=[SourceBand+'.feather_'+spw7m+'_and_'+spwTP+'.image',Parent7m+'.pb.subimage'],
       expr='IM0/IM1',
       outfile=SourceBand+'.feather_'+spw7m+'_and_'+spwTP+'.image.pbcor')

#### For additional help, check out mhoffies on github where M. Hoffman has script for feathering 12m and GBT data.
