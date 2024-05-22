import json
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets,status
from .models import CustomerModel, CustomerDocumentModel, CountryModel, DocumentSetModel
from .serializers import CustomerSerializer, CustomerDocumentSerializer, CountrySerializer, DocumentSetSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import boto3
from django.utils import timezone
from django.contrib.auth.models import User
import spacy
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.uploadedfile import UploadedFile
import logging


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        # Generate session token
        session_token = generate_session_token(user)

        # Return the session token and user data in the response
        return Response({'message': 'Login successful', 'session_token': session_token, 'user': user.id}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

def generate_session_token(user):
    # Use user's ID as the session token
    session_token = str(user.id)
    return session_token




@csrf_exempt
def extract_details_from_id(request):
    print('itshere')
    
    # Configure AWS credentials and region
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_default_region = os.environ.get('AWS_DEFAULT_REGION')
    
    logger = logging.getLogger(__name__)
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)
    
    files = request.FILES.getlist('file')  # Get list of uploaded files

    session_token = request.POST.get('session_token')
    user_id = request.POST.get('user_id')

   
    
    try:
        boto3.setup_default_session(
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key, 
            region_name=aws_default_region
        )

        s3_client = boto3.client('s3', region_name=aws_default_region)
        textract_client = boto3.client('textract')

        bucket_name = 'idprooftest'

        extracted_data_dict = {}

        for index, file_obj in enumerate(files, start=1):
            object_key = file_obj.name
           
            # Upload file to S3 bucket
            s3_client.upload_fileobj(file_obj, bucket_name, object_key)
            
            # Log the object details for debugging
            logger.info(f"Uploaded file to S3: Bucket={bucket_name}, Key={object_key}")
            print(f"Uploaded file to S3: Bucket={bucket_name}, Key={object_key}")
            
            # Prepare arguments for analyze_id API call with S3 object reference
            document = {'S3Object': {'Bucket': bucket_name, 'Name': object_key}}
            s3_object = {
                'Bucket': bucket_name,
                'Name': object_key
            }
           
            # Call Textract's analyze_id method
            response = textract_client.analyze_id(DocumentPages=[{'S3Object': s3_object}])
          
            # Process extracted data
            for field in response['IdentityDocuments'][0]['IdentityDocumentFields']:
                field_type = field['Type']['Text']
                field_value = field['ValueDetection']['Text']
                if field_type not in extracted_data_dict or extracted_data_dict[field_type] is None:
                    extracted_data_dict[field_type] = field_value
                else:
                    # Update the value if it is null
                    extracted_data_dict[field_type] = field_value
            # save_customer_document(session_token, file_obj, extracted_data_dict)

        return JsonResponse({'extracted_data': extracted_data_dict})

    except boto3.exceptions.S3UploadFailedError as e:
        logger.error(f"S3 upload failed: {e}")
        return JsonResponse({'error': 'Failed to upload file to S3.'}, status=500)
    except boto3.exceptions.Boto3Error as e:
        logger.error(f"Boto3 error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except User.DoesNotExist:
        logger.error("User not found.")
        return JsonResponse({'error': 'User not found.'}, status=404)
    except CountryModel.DoesNotExist:
        logger.error("Country model not found.")
        return JsonResponse({'error': 'Country model not found.'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def save_details(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)
    
    data = json.loads(request.body)
    session_token = data.get('session_token')
  
    user = User.objects.get(id = session_token)
    country = user.countries.first()
    print(user)
    try:
        customer = CustomerModel(
            surname=data.get('LAST_NAME'),
            first_name=data.get('FIRST_NAME'),
            nationality_id=country.id, 
            gender=data.get('GENDER','O'),
            created_by=user  
        )
        customer.save()
        return JsonResponse({'success': 'Details saved successfully!'})
    except Exception as e:
        print(str(e))
        return JsonResponse({'error': str(e)}, status=500)    

@csrf_exempt
def list_customers(request):
    session_token = request.GET.get('session_token')
    
    if not session_token:
        return JsonResponse({'error': 'Session token is required'}, status=400)
    
    try:
        user = User.objects.get(id=session_token)
        customers = CustomerModel.objects.filter(created_by=user)
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'id': customer.id,
                'first_name': customer.first_name,
                'surname': customer.surname,
                'nationality': {
                    'id': customer.nationality.id,
                    'name': customer.nationality.name
                } 
            })

        return JsonResponse(customer_data, safe=False)

    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid session token'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_country(request):
    if request.method == 'GET':
        session_token = request.GET.get('session_token')
        if session_token:
            try:
                user = User.objects.get(id=session_token)
                country_id = user.country_id
                if country_id:
                    country_name = CountryModel.objects.get(id=country_id).name
                    return JsonResponse({'country_id': country_id, 'country_name': country_name})
                else:
                    return JsonResponse({'error': 'User has no associated country.'}, status=404)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found.'}, status=404)
        else:
            return JsonResponse({'error': 'Session token not provided.'}, status=400)
    else:
        return JsonResponse({'error': 'Only GET requests allowed.'}, status=405)


# def save_customer_document(customer, image_file, details):
#     user = User.objects.get(id=customer)
#     customer_document = CustomerDocumentModel(
#         customer=user,
#         document=image_file,
#         details=json.dumps(details)
#     )
#     customer_document.save()















class CountryViewSet(viewsets.ModelViewSet):
    queryset = CountryModel.objects.all()
    serializer_class = CountrySerializer

class DocumentSetViewSet(viewsets.ModelViewSet):
    queryset = DocumentSetModel.objects.all()
    serializer_class = DocumentSetSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = CustomerModel.objects.all()
    serializer_class = CustomerSerializer

class CustomerDocumentViewSet(viewsets.ModelViewSet):
    queryset = CustomerDocumentModel.objects.all()
    serializer_class = CustomerDocumentSerializer

