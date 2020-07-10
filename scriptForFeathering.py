"""
This script allows you to feather high- and low-resolution data,
specifically those observed with ALMA.

This script is not intended to be executed in its entirety.
Rather, you should copy lines into CASA and make adjustments as necessary.

Commands should be executed in the directory where you would like the 
final feathered images to be stored. Intermediate files will be stored
in this directory as well. 

Script compiled by O. H. Wilkins with the help of S. Wood and M. Hoffman.

"""

####################
###### INPUTS ######
####################

# Enter the naming conventions you'd like to use 
# to keep track of your data sets and for file names.
# TP = Total Power (or low-resolution data)
# 7m = ACA (or high-resolution data)

SourceName = 'BGPS3053'
BandName = 'upper'
SourceBand = SourceName+'_'+BandName
spwTP = 'spw17_TP'
spw7m = 'spw16_7m'

# Enter the path to the FITS image for the low-resolution data
# you'd like to import for feathering.
TPfits = '../member.uid___A001_X133d_X2db7/product/member.uid___A001_X133d_X2db7.BGPS3053.spw17.I.sd.im.fits'
ACAimage = '../member.uid___A001_X133d_X2db5/calibrated/BGPS3053_upper.spw16_CH3OH.image'

# Enter the path for the CASA image for the high-resolution 
# data you'd like to feather. 
ACApb = '../member.uid___A001_X133d_X2db5/calibrated/BGPS3053_upper.spw16_CH3OH.pb'


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
imreframe(imagename=ParentTP+'.image',restfreq='241843649999.99997Hz')


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
Box = '30,30,315,330'

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
