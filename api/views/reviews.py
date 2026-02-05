from rest_framework import response, status
from rest_framework.views import APIView
from ..mongo_utils import get_db_handle
from datetime import datetime
from bson import ObjectId
from django.contrib.auth.models import User

class ReviewList(APIView):
    # API view to manage Reviews using MongoDB
    
    def get(self, request):
        # List all reviews or filter by product_id
        db = get_db_handle()
        collection = db['reviews']
        
        product_id = request.query_params.get('product_id')
        filter_query = {}
        if product_id:
            filter_query['product_id'] = int(product_id)
        
        # Convert ObjectId to string for JSON serialization
        reviews = list(collection.find(filter_query))
        
        # Enrich with User data from SQL
        user_ids = [review.get('user_id') for review in reviews if review.get('user_id')]
        users = User.objects.filter(id__in=user_ids).values('id', 'username')
        user_map = {user['id']: user['username'] for user in users}

        for review in reviews:
            review['_id'] = str(review['_id'])
            user_id = review.get('user_id')
            review['username'] = user_map.get(user_id, "Unknown User")
            
        return response.Response(reviews)

    def post(self, request):
        # Create a new review
        # Sample Data:
        {
            "product_id": 1,
            "user_id": 1,
            "rating": 5,
            "comment": "Great product!"
        }
        db = get_db_handle()
        collection = db['reviews']
        
        data = request.data
        review = {
            'product_id': data.get('product_id'),
            'user_id': data.get('user_id'),
            'rating': data.get('rating'),
            'comment': data.get('comment'),
            'created_at': datetime.now().isoformat()
        }
        
        result = collection.insert_one(review)
        review['_id'] = str(result.inserted_id)
        
        return response.Response(review, status=status.HTTP_201_CREATED)

class ReviewDetail(APIView):
    # API view to retrieve, update or delete a specific review from MongoDB
    
    def get_object(self, pk):
        db = get_db_handle()
        collection = db['reviews']
        try:
            return collection.find_one({'_id': ObjectId(pk)})
        except:
            return None

    def get(self, request, pk):
        review = self.get_object(pk)
        if review:
            review['_id'] = str(review['_id'])
            return response.Response(review)
        return response.Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        db = get_db_handle()
        collection = db['reviews']
        
        existing_review = self.get_object(pk)
        if not existing_review:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data
        update_data = {k: v for k, v in data.items() if k in ['rating', 'comment', 'product_id', 'user_id']}
        update_data['updated_at'] = datetime.now().isoformat()
        
        collection.update_one({'_id': ObjectId(pk)}, {'$set': update_data})
        
        updated_review = collection.find_one({'_id': ObjectId(pk)})
        updated_review['_id'] = str(updated_review['_id'])
        
        return response.Response(updated_review)

    def delete(self, request, pk):
        db = get_db_handle()
        collection = db['reviews']
        
        result = collection.delete_one({'_id': ObjectId(pk)})
        if result.deleted_count > 0:
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(status=status.HTTP_404_NOT_FOUND)
