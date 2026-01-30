import os
import tempfile
import json
import shutil
from django.shortcuts import render
from django.http import HttpResponse, FileResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .core import compare_files_logic, apply_patch_logic

def dashboard(request):
    return render(request, 'dashboard.html')

class CompareAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'original' not in request.FILES or 'modified' not in request.FILES:
            return Response({"error": "Missing files"}, status=400)

        orig_file = request.FILES['original']
        mod_file = request.FILES['modified']

        # Save to temp files
        with tempfile.NamedTemporaryFile(delete=False) as t1, tempfile.NamedTemporaryFile(delete=False) as t2:
            for chunk in orig_file.chunks(): t1.write(chunk)
            for chunk in mod_file.chunks(): t2.write(chunk)
            t1_name = t1.name
            t2_name = t2.name

        try:
            result = compare_files_logic(t1_name, t2_name)
            return Response(result)
        finally:
            if os.path.exists(t1_name): os.unlink(t1_name)
            if os.path.exists(t2_name): os.unlink(t2_name)

class PatchAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'target' not in request.FILES or 'patch' not in request.data:
            return Response({"error": "Missing target file or patch data"}, status=400)

        target_file = request.FILES['target']
        try:
           patch_data = json.loads(request.data['patch'])
        except:
           patch_data = request.data['patch'] # Might already be dict if DRF handled it, but usually it's a string in multipart

        # Save target to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix="_target") as t1:
            for chunk in target_file.chunks(): t1.write(chunk)
            t1_name = t1.name

        out_path = None
        try:
            out_path, modifications = apply_patch_logic(t1_name, patch_data)
            
            # Open the generated file and return it
            # We use FileResponse. 
            # cleanup is tricky with FileResponse since it needs the file open.
            # We can read it into memory if small, or use a cleanup callback.
            # Given typical ROM patches, memory is fine.
            
            with open(out_path, 'rb') as f:
                file_data = f.read()
                
            response = HttpResponse(file_data, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="Edited_by_Jomberykaso_{target_file.name}"'
            return response
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            if os.path.exists(t1_name): os.unlink(t1_name)
            if out_path and os.path.exists(out_path): os.unlink(out_path)
