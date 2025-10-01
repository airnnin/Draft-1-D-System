from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.serializers import geojson
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import HazardDataset, FloodSusceptibility, LandslideSusceptibility, LiquefactionSusceptibility
from .utils import ShapefileProcessor
import json

def index(request):
    """Main map view"""
    return render(request, 'index.html')

@csrf_exempt
@api_view(['POST'])
def upload_shapefile(request):
    """Handle shapefile upload and processing"""
    if request.method == 'POST':
        if 'shapefile' not in request.FILES:
            return JsonResponse({'error': 'No shapefile provided'}, status=400)
        
        if 'dataset_type' not in request.POST:
            return JsonResponse({'error': 'Dataset type not specified'}, status=400)
        
        uploaded_file = request.FILES['shapefile']
        dataset_type = request.POST['dataset_type']
        
        # Validate dataset type
        valid_types = ['flood', 'landslide', 'liquefaction']
        if dataset_type not in valid_types:
            return JsonResponse({'error': f'Invalid dataset type. Must be one of: {valid_types}'}, status=400)
        
        # Process the shapefile
        processor = ShapefileProcessor(uploaded_file, dataset_type)
        result = processor.process()
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def get_flood_data(request):
    """Get flood susceptibility data as GeoJSON"""
    try:
        # Get all flood susceptibility records
        flood_features = []
        flood_records = FloodSusceptibility.objects.all()
        
        for record in flood_records:
            feature = {
                'type': 'Feature',
                'properties': {
                    'susceptibility': record.flood_susc,
                    'original_code': record.original_code,
                    'shape_area': record.shape_area,
                    'dataset_id': record.dataset.id
                },
                'geometry': json.loads(record.geometry.geojson)
            }
            flood_features.append(feature)
        
        geojson_data = {
            'type': 'FeatureCollection',
            'features': flood_features
        }
        
        return Response(geojson_data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_landslide_data(request):
    """Get landslide susceptibility data as GeoJSON"""
    try:
        landslide_features = []
        landslide_records = LandslideSusceptibility.objects.all()
        
        for record in landslide_records:
            feature = {
                'type': 'Feature',
                'properties': {
                    'susceptibility': record.landslide_susc,
                    'original_code': record.original_code,
                    'shape_area': record.shape_area,
                    'dataset_id': record.dataset.id
                },
                'geometry': json.loads(record.geometry.geojson)
            }
            landslide_features.append(feature)
        
        geojson_data = {
            'type': 'FeatureCollection',
            'features': landslide_features
        }
        
        return Response(geojson_data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_liquefaction_data(request):
    """Get liquefaction susceptibility data as GeoJSON"""
    try:
        liquefaction_features = []
        liquefaction_records = LiquefactionSusceptibility.objects.all()
        
        for record in liquefaction_records:
            feature = {
                'type': 'Feature',
                'properties': {
                    'susceptibility': record.liquefaction_susc,
                    'original_code': record.original_code,
                    'dataset_id': record.dataset.id
                },
                'geometry': json.loads(record.geometry.geojson)
            }
            liquefaction_features.append(feature)
        
        geojson_data = {
            'type': 'FeatureCollection',
            'features': liquefaction_features
        }
        
        return Response(geojson_data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_datasets(request):
    """Get list of uploaded datasets"""
    try:
        datasets = HazardDataset.objects.all().values(
            'id', 'name', 'dataset_type', 'upload_date', 'file_name'
        )
        return Response(list(datasets))
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)