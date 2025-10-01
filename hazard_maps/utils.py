import fiona
import zipfile
import os
import tempfile
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.core.files.storage import default_storage
from .models import HazardDataset, FloodSusceptibility, LandslideSusceptibility, LiquefactionSusceptibility
import json

class ShapefileProcessor:
    """Process and standardize shapefile data"""
    
    # Standardization mappings from your document
    FLOOD_MAPPING = {
        'LF': 'LS',   # Low Flood → Low Susceptibility
        'MF': 'MS',   # Moderate Flood → Moderate Susceptibility (updated from your data)
        'HF': 'HS',   # High Flood → High Susceptibility
        'VHF': 'VHS'  # Very High Flood → Very High Susceptibility
    }
    
    LANDSLIDE_MAPPING = {
        'LL': 'LS',   # Low Landslide → Low Susceptibility
        'ML': 'MS',   # Moderate → Moderate Susceptibility
        'HL': 'HS',   # High Landslide → High Susceptibility
        'VHL': 'VHS', # Very High Landslide → Very High Susceptibility
        'DF': 'DF'    # Unknown classification
    }
    
    LIQUEFACTION_MAPPING = {
        'Low Susceptibility': 'LS',
        'Moderate Susceptibility': 'MS', 
        'High Susceptibility': 'HS',
        'Low susceptibility': 'LS',      # Handle case variations
        'Moderate susceptibility': 'MS',
        'High susceptibility': 'HS'
    }
    
    def __init__(self, uploaded_file, dataset_type):
        self.uploaded_file = uploaded_file
        self.dataset_type = dataset_type
        self.temp_dir = None
        
    def extract_shapefile(self):
        """Extract shapefile from uploaded zip"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Save uploaded file temporarily
        temp_zip_path = os.path.join(self.temp_dir, 'shapefile.zip')
        with open(temp_zip_path, 'wb') as temp_file:
            for chunk in self.uploaded_file.chunks():
                temp_file.write(chunk)
        
        # Extract zip file
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        
        # Find .shp file
        shp_file = None
        for file in os.listdir(self.temp_dir):
            if file.endswith('.shp'):
                shp_file = os.path.join(self.temp_dir, file)
                break
                
        if not shp_file:
            raise ValueError("No .shp file found in the uploaded zip")
            
        return shp_file
    
    def standardize_code(self, original_code, dataset_type):
        """Standardize susceptibility codes based on dataset type"""
        original_code = str(original_code).strip()
        
        if dataset_type == 'flood':
            return self.FLOOD_MAPPING.get(original_code, original_code)
        elif dataset_type == 'landslide':
            return self.LANDSLIDE_MAPPING.get(original_code, original_code)
        elif dataset_type == 'liquefaction':
            # Handle case-insensitive matching for liquefaction
            for key, value in self.LIQUEFACTION_MAPPING.items():
                if original_code.lower() == key.lower():
                    return value
            return 'LS'  # Default to Low if not found
        
        return original_code
    
    def transform_geometry(self, geom_dict, source_crs):
        """Transform geometry to EPSG:4253 with proper error handling"""
        try:
            # Import json to ensure proper formatting
            import json
            
            # Convert fiona.Geometry to proper dictionary
            if hasattr(geom_dict, '__geo_interface__'):
                # Use the __geo_interface__ property to get the GeoJSON-like dict
                geom_data = geom_dict.__geo_interface__
            else:
                geom_data = geom_dict
            
            # Create GEOSGeometry from JSON string
            geometry = GEOSGeometry(json.dumps(geom_data))
            
            # Set SRID to 4253 (your target CRS)
            geometry.srid = 4253
            
            # Ensure it's a MultiPolygon
            if geometry.geom_type == 'Polygon':
                # Convert Polygon to MultiPolygon
                from django.contrib.gis.geos import MultiPolygon
                geometry = MultiPolygon(geometry)
            
            return geometry
            
        except Exception as e:
            print(f"Geometry transformation error: {e}")
            print(f"Geometry object type: {type(geom_dict)}")
            print(f"Has __geo_interface__: {hasattr(geom_dict, '__geo_interface__')}")
            if hasattr(geom_dict, '__geo_interface__'):
                print(f"Geo interface: {geom_dict.__geo_interface__}")
            raise
    
    def process_flood_data(self, shp_file, dataset):
        """Process flood susceptibility shapefile"""
        records_created = 0
        errors = []
        
        try:
            with fiona.open(shp_file) as shapefile:
                print(f"Shapefile CRS: {shapefile.crs}")
                print(f"Schema: {shapefile.schema}")
                print(f"Total features: {len(shapefile)}")
                
                for idx, feature in enumerate(shapefile):
                    try:
                        # Extract properties
                        props = feature['properties']
                        geom = feature['geometry']
                        
                        if geom is None:
                            print(f"Skipping feature {idx}: No geometry")
                            continue
                        
                        # Get original code and standardize
                        original_code = props.get('FloodSusc', '')
                        standardized_code = self.standardize_code(original_code, 'flood')
                        
                        # Debug output for first few features
                        if records_created < 5:
                            print(f"Flood feature {records_created}: '{original_code}' -> '{standardized_code}'")
                        
                        # Transform geometry
                        geometry = self.transform_geometry(geom, shapefile.crs)
                        
                        # Create database record
                        FloodSusceptibility.objects.create(
                            dataset=dataset,
                            flood_susc=standardized_code,
                            original_code=original_code,
                            shape_length=props.get('SHAPE_Leng'),
                            shape_area=props.get('SHAPE_Area'),
                            orig_fid=props.get('ORIG_FID'),
                            geometry=geometry
                        )
                        records_created += 1
                        
                        if records_created % 100 == 0:
                            print(f"Processed {records_created} features...")
                        
                    except Exception as feature_error:
                        error_msg = f"Error processing feature {idx}: {feature_error}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue
                        
        except Exception as file_error:
            print(f"Error opening shapefile: {file_error}")
            raise
        
        if errors:
            print(f"Completed with {len(errors)} errors")
            
        return records_created
    
    def process_landslide_data(self, shp_file, dataset):
        """Process landslide susceptibility shapefile"""
        records_created = 0
        
        with fiona.open(shp_file) as shapefile:
            print(f"Processing landslide data, CRS: {shapefile.crs}")
            
            for idx, feature in enumerate(shapefile):
                try:
                    props = feature['properties']
                    geom = feature['geometry']
                    
                    if geom is None:
                        continue
                    
                    # Get original code and standardize - try both field names
                    original_code = props.get('LndslideSu') or props.get('LndSu', '')
                    standardized_code = self.standardize_code(original_code, 'landslide')
                    
                    # Transform geometry
                    geometry = self.transform_geometry(geom, shapefile.crs)
                    
                    # Create database record
                    LandslideSusceptibility.objects.create(
                        dataset=dataset,
                        landslide_susc=standardized_code,
                        original_code=original_code,
                        shape_length=props.get('SHAPE_Leng'),
                        shape_area=props.get('SHAPE_Area'),
                        orig_fid=props.get('ORIG_FID'),
                        geometry=geometry
                    )
                    records_created += 1
                    
                except Exception as e:
                    print(f"Error processing landslide feature {idx}: {e}")
                    continue
                
        return records_created
    
    def process_liquefaction_data(self, shp_file, dataset):
        """Process liquefaction susceptibility shapefile"""
        records_created = 0
        
        with fiona.open(shp_file) as shapefile:
            print(f"Processing liquefaction data, CRS: {shapefile.crs}")
            
            for idx, feature in enumerate(shapefile):
                try:
                    props = feature['properties']
                    geom = feature['geometry']
                    
                    if geom is None:
                        continue
                    
                    # Get original code and standardize - handle variations in field values
                    original_code = props.get('Susceptibi', '').strip()
                    standardized_code = self.standardize_code(original_code, 'liquefaction')
                    
                    # Debug output
                    print(f"Liquefaction feature {idx}: '{original_code}' -> '{standardized_code}'")
                    
                    # Transform geometry
                    geometry = self.transform_geometry(geom, shapefile.crs)
                    
                    # Create database record
                    LiquefactionSusceptibility.objects.create(
                        dataset=dataset,
                        liquefaction_susc=standardized_code,
                        original_code=original_code,
                        geometry=geometry
                    )
                    records_created += 1
                    
                except Exception as e:
                    print(f"Error processing liquefaction feature {idx}: {e}")
                    continue
                
        return records_created
    
    def process(self):
        """Main processing method"""
        try:
            # Extract shapefile
            shp_file = self.extract_shapefile()
            
            # Create dataset record
            dataset = HazardDataset.objects.create(
                name=f"Uploaded {self.dataset_type.title()} Data",
                dataset_type=self.dataset_type,
                file_name=self.uploaded_file.name
            )
            
            # Process based on dataset type
            if self.dataset_type == 'flood':
                records_created = self.process_flood_data(shp_file, dataset)
            elif self.dataset_type == 'landslide':
                records_created = self.process_landslide_data(shp_file, dataset)
            elif self.dataset_type == 'liquefaction':
                records_created = self.process_liquefaction_data(shp_file, dataset)
            else:
                raise ValueError(f"Unsupported dataset type: {self.dataset_type}")
            
            return {
                'success': True,
                'dataset_id': dataset.id,
                'records_created': records_created,
                'message': f'Successfully processed {records_created} records'
            }
            
        except Exception as e:
            print(f"Processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
        finally:
            # Cleanup temporary files
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)