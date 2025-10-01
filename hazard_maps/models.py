from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
import json

class HazardDataset(models.Model):
    """Model to track uploaded datasets"""
    DATASET_TYPES = [
        ('flood', 'Flood Susceptibility'),
        ('landslide', 'Landslide Susceptibility'),
        ('liquefaction', 'Liquefaction Susceptibility'),
        ('sea_level_rise', 'Sea Level Rise'),
        ('zonal_values', 'Zonal Values'),
    ]
    
    name = models.CharField(max_length=200)
    dataset_type = models.CharField(max_length=20, choices=DATASET_TYPES)
    upload_date = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_dataset_type_display()})"

class FloodSusceptibility(models.Model):
    """Model for flood susceptibility data"""
    SUSCEPTIBILITY_LEVELS = [
        ('LS', 'Low Susceptibility'),
        ('MS', 'Moderate Susceptibility'),
        ('HS', 'High Susceptibility'),
        ('VHS', 'Very High Susceptibility'),
    ]
    
    dataset = models.ForeignKey(HazardDataset, on_delete=models.CASCADE)
    flood_susc = models.CharField(max_length=3, choices=SUSCEPTIBILITY_LEVELS)
    original_code = models.CharField(max_length=10)  # Store original code for reference
    shape_length = models.FloatField(null=True, blank=True)
    shape_area = models.FloatField(null=True, blank=True)
    orig_fid = models.IntegerField(null=True, blank=True)
    geometry = models.MultiPolygonField(srid=4253)  # EPSG:4253 as per your data
    
    def __str__(self):
        return f"Flood {self.flood_susc} - FID: {self.orig_fid}"

class LandslideSusceptibility(models.Model):
    """Model for landslide susceptibility data"""
    SUSCEPTIBILITY_LEVELS = [
        ('LS', 'Low Susceptibility'),
        ('MS', 'Moderate Susceptibility'),
        ('HS', 'High Susceptibility'),
        ('VHS', 'Very High Susceptibility'),
        ('DF', 'Unknown Classification'),
    ]
    
    dataset = models.ForeignKey(HazardDataset, on_delete=models.CASCADE)
    landslide_susc = models.CharField(max_length=3, choices=SUSCEPTIBILITY_LEVELS)
    original_code = models.CharField(max_length=10)
    shape_length = models.FloatField(null=True, blank=True)
    shape_area = models.FloatField(null=True, blank=True)
    orig_fid = models.IntegerField(null=True, blank=True)
    geometry = models.MultiPolygonField(srid=4253)
    
    def __str__(self):
        return f"Landslide {self.landslide_susc} - FID: {self.orig_fid}"

class LiquefactionSusceptibility(models.Model):
    """Model for liquefaction susceptibility data"""
    SUSCEPTIBILITY_LEVELS = [
        ('LS', 'Low Susceptibility'),
        ('MS', 'Moderate Susceptibility'),
        ('HS', 'High Susceptibility'),
    ]
    
    dataset = models.ForeignKey(HazardDataset, on_delete=models.CASCADE)
    liquefaction_susc = models.CharField(max_length=3, choices=SUSCEPTIBILITY_LEVELS)
    original_code = models.CharField(max_length=50)  # Longer for "Low Susceptibility" text
    geometry = models.MultiPolygonField(srid=4253)
    
    def __str__(self):
        return f"Liquefaction {self.liquefaction_susc}"