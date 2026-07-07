import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from .utils import get_db_collection, process_and_store_csv

def login_view(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    collection = get_db_collection()
    
    total_records = collection.count_documents({})
    
    # Auto-load data from local CSV if database doesn't have the full dataset
    if total_records < 1000:
        csv_path = os.path.join(settings.BASE_DIR, 'marine_pollution_data.csv')
        if os.path.exists(csv_path):
            process_and_store_csv(csv_path)
            total_records = collection.count_documents({})
    
    all_docs = list(collection.find({}, {'_id': 0, 'pollution_level': 1, 'location': 1, 'pollution_status': 1}))
    
    avg_pollution = 0
    highly_polluted = []
    
    if total_records > 0:
        total_p = sum(doc.get('pollution_level', 0) for doc in all_docs)
        avg_pollution = round(total_p / total_records, 2)
        
        # NumPy use case - extract array and find mean/max
        p_levels = np.array([doc.get('pollution_level', 0) for doc in all_docs])
        std_dev = round(np.std(p_levels), 2)
        max_p = np.max(p_levels)
        min_p = np.min(p_levels)
        
        # Highly polluted
        high_docs = [doc for doc in all_docs if doc.get('pollution_status') == 'High']
        
        # Group by location simply
        loc_counts = {}
        for d in high_docs:
            l = d.get('location')
            loc_counts[l] = loc_counts.get(l, 0) + 1
            
        highly_polluted = sorted(loc_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    else:
        std_dev, max_p, min_p = 0, 0, 0
        
    context = {
        'total_records': total_records,
        'avg_pollution': avg_pollution,
        'highly_polluted': highly_polluted,
        'std_dev': std_dev,
        'max_p': max_p,
        'min_p': min_p
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def analysis_view(request):
    collection = get_db_collection()
    data = list(collection.find({}, {'_id': 0}))
    
    if not data:
        messages.warning(request, "No data available for analysis. Please upload a dataset first.")
        return render(request, 'analysis.html', {'images': []})
        
    df = pd.DataFrame(data)
    
    static_img_dir = os.path.join(settings.BASE_DIR, 'pollution_app', 'static', 'images')
    os.makedirs(static_img_dir, exist_ok=True)
    
    # 1. Line Chart -> Pollution trend over time (Using first 50 sorted by date)
    plt.figure(figsize=(10, 5))
    df_sorted = df.sort_values(by='date').head(50)
    plt.plot(df_sorted['date'], df_sorted['pollution_level'], marker='o', linestyle='-', color='dodgerblue')
    plt.title('Pollution Trend Over Time (Sample)')
    plt.xlabel('Date')
    plt.ylabel('Pollution Level')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(static_img_dir, 'trend.png'))
    plt.close()
    
    # 2. Bar Chart -> Avg Pollution by location
    plt.figure(figsize=(10, 5))
    loc_mean = df.groupby('location')['pollution_level'].mean().sort_values(ascending=False).head(10)
    loc_mean.plot(kind='bar', color='coral')
    plt.title('Average Pollution by Location')
    plt.xlabel('Location')
    plt.ylabel('Avg Pollution Level')
    plt.ylim(bottom=max(0, loc_mean.min() - 5), top=loc_mean.max() + 5)
    plt.tight_layout()
    plt.savefig(os.path.join(static_img_dir, 'location_bar.png'))
    plt.close()

    # 3. Pie Chart -> Pollution distribution
    plt.figure(figsize=(8, 8))
    status_counts = df['pollution_status'].value_counts()
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99'])
    plt.title('Pollution Status Distribution')
    plt.tight_layout()
    plt.savefig(os.path.join(static_img_dir, 'status_pie.png'))
    plt.close()

    # 4. Scatter Plot -> Temperature vs Pollution
    plt.figure(figsize=(8, 6))
    plt.scatter(df['temperature'], df['pollution_level'], alpha=0.5, c='purple')
    plt.title('Temperature vs Pollution Level')
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Pollution Level')
    plt.tight_layout()
    plt.savefig(os.path.join(static_img_dir, 'scatter.png'))
    plt.close()

    return render(request, 'analysis.html')

@login_required(login_url='login')
def search_filter_view(request):
    collection = get_db_collection()
    query = {}
    
    record_id = request.GET.get('record_id')
    if record_id and record_id.isdigit():
        query['record_id'] = int(record_id)
        
    loc = request.GET.get('location')
    if loc:
        query['location'] = {'$regex': loc, '$options': 'i'}
        
    status = request.GET.get('status')
    if status:
        query['pollution_status'] = status
        
    oil = request.GET.get('oil_spill')
    if oil:
        query['oil_spill'] = oil
        
    records = list(collection.find(query, {'_id': 0}))
    
    return render(request, 'report.html', {'records': records})

@login_required(login_url='login')
def generate_report_view(request):
    # Retrieve filtered data (simple re-use of GET params)
    collection = get_db_collection()
    query = {}
    
    status = request.GET.get('status')
    if status:
        query['pollution_status'] = status
        
    records = list(collection.find(query, {'_id': 0}))
    
    if not records:
        return HttpResponse("No data to download", status=404)
        
    df = pd.DataFrame(records)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="marine_pollution_report.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response
