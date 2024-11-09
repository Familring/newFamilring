from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import User
from django.http import JsonResponse
from .models import DailyQuestion
import openai
from datetime import date
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, BucketList, Family, FamilyRequest, FamilyList, Answer
from .serializers import UserSerializer, BucketListSerializer, FamilySerializer, \
    FamilyRequestSerializer
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.middleware.csrf import get_token
from .models import UserFontSetting


@api_view(['GET'])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return Response({'csrfToken': csrf_token})

# 회원가입
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])  # 인증이 필요하지 않도록 설정
def register(request):
    data = request.data.copy()
    data['password'] = make_password(data['password'])
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['POST'])
@permission_classes([AllowAny])  # 누구나 접근 가능하게 설정
def login(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')

    # 사용자 인증
    user = authenticate(request, username=username, password=password)
    if user is not None:
        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        # 사용자에 연결된 family 정보 가져오기
        family = Family.objects.filter(user_id=user).first()  # `user_id`로 수정
        family_id = family.family_id if family else None


        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'username': user.username,
            'family_id': family_id,
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid username or password'}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Family, FamilyList, BucketList
from .serializers import BucketListSerializer
from django.shortcuts import get_object_or_404

# 가족 및 개인 버킷리스트 가져오기
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bucketlists(request):
    user = request.user
    family_list_entry = FamilyList.objects.filter(user=user).first()

    # 개인 버킷리스트
    personal_bucketlist = BucketList.objects.filter(user=user, family__isnull=True)

    # 가족 버킷리스트
    family_bucketlist = []
    if family_list_entry:
        family = family_list_entry.family
        family_bucketlist = BucketList.objects.filter(family=family, user__isnull=True)

    personal_serializer = BucketListSerializer(personal_bucketlist, many=True)
    family_serializer = BucketListSerializer(family_bucketlist, many=True)

    return Response(
        {
            'personal_bucket_list': personal_serializer.data,
            'family_bucket_list': family_serializer.data
        },
        status=status.HTTP_200_OK,
        content_type='application/json; charset=utf-8'
    )

# 버킷리스트 추가하기
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bucketlist(request):
    user = request.user
    is_family_bucket = request.data.get('is_family_bucket', False)

    if is_family_bucket:
        # 가족 버킷리스트로 추가
        family_list_entry = FamilyList.objects.filter(user=user).first()
        if not family_list_entry:
            return Response({'error': 'No family associated with this user'}, status=status.HTTP_400_BAD_REQUEST)

        family = family_list_entry.family
        data = {
            'family': family.family_id,
            'bucket_title': request.data['bucket_title'],
            'is_completed': False,
        }
    else:
        # 개인 버킷리스트로 추가
        data = {
            'user': user.id,
            'bucket_title': request.data['bucket_title'],
            'is_completed': False,
        }

    serializer = BucketListSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import BucketList
from django.shortcuts import get_object_or_404
from rest_framework import status

# 버킷리스트 완료 처리
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def complete_bucketlist(request, bucket_id):
    #print(f"Received request to update bucket with ID: {bucket_id}")
    user = request.user
    is_family_bucket = request.data.get('is_family_bucket', False)

    if is_family_bucket:
        # 가족 버킷리스트 완료 처리
        family_list_entry = FamilyList.objects.filter(user=user).first()
        if not family_list_entry:
            return Response({'error': 'No family associated with this user'}, status=status.HTTP_400_BAD_REQUEST)

        family = family_list_entry.family
        bucketlist = get_object_or_404(BucketList, bucket_id=bucket_id, family=family, user__isnull=True)
    else:
        # 개인 버킷리스트 완료 처리
        bucketlist = get_object_or_404(BucketList, bucket_id=bucket_id, user=request.user, family__isnull=True)

    bucketlist.is_completed = True
    bucketlist.save()
    return Response({"message": "버킷리스트가 완료되었습니다."}, status=status.HTTP_200_OK)

from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer

@api_view(['GET'])
def get_profile(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['PUT'])
def update_profile(request):
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def get_all_users(request):
    cUser = request.user  # 요청한 사용자
    users = User.objects.exclude(id=cUser.id)  # 요청한 사용자를 제외한 사용자
    serializer = UserSerializer(users, many=True)
    return Response(
        serializer.data,
        status=200,
        content_type='application/json; charset=utf-8'
    )
# 가족 생성 API
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User, Family, FamilyList, FamilyRequest
from .serializers import UserSerializer, FamilyRequestSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_family(request):
    family_name = request.data.get('family_name')
    if not family_name:
        return Response({"error": "Family name is required"}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자가 속한 가족이 없는지 확인
    has_family = Family.objects.filter(user=request.user).exists() or FamilyList.objects.filter(user=request.user).exists()
    if has_family:
        return Response({"error": "이미 가족이 존재합니다. 가족 삭제 후 다시 생성할 수 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 새로운 가족 생성
    family = Family.objects.create(
        family_name=family_name,
        user=request.user
    )

    # 첫 번째 사용자를 가족 목록에 추가
    FamilyList.objects.create(family=family, user=request.user)

    return Response(
        {
            "family_id": family.family_id,
            "family_name": family.family_name,
            "message": "가족이 성공적으로 생성되었습니다."
        },
        status=status.HTTP_201_CREATED
    )


# 사용자 검색 기능 (로그인한 사용자와 이미 가족 구성원인 사용자 제외)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_user(request):
    username = request.GET.get('username')
    if not username:
        return Response(
            {'error': 'Username parameter is required'},
            status=400,
            content_type='application/json; charset=utf-8'
        )

    # 검색된 사용자를 가져오되, 로그인한 사용자 및 이미 가족 구성원인 사용자를 제외
    users = User.objects.exclude(id=request.user.id)

    # 로그인한 사용자가 속한 가족 구성원을 가져오기
    family_members = FamilyList.objects.filter(family__user_id=request.user).values_list('user_id', flat=True)
    users = users.exclude(id__in=family_members)

    # 검색어와 일치하는 사용자 필터링
    users = users.filter(username__icontains=username)

    # 시리얼라이즈 후 응답
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=200)


# 가족 초대 요청 생성
@api_view(['POST'])
def send_family_invitation(request):
    data = request.data
    from_user = request.user
    to_user = get_object_or_404(User, id=data['to_user_id'])

    # from_user의 family를 가져오기
    try:
        family = Family.objects.get(user=from_user)  # Family와 User가 연결된 부분
    except Family.DoesNotExist:
        return Response({"error": "사용자의 가족 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 이미 초대된 사용자인지 확인
    if FamilyRequest.objects.filter(from_user=from_user, to_user=to_user, family=family).exists():
        return Response({"error": "이미 가족 초대를 보냈습니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 가족 초대 요청 생성
    FamilyRequest.objects.create(
        from_user=from_user,
        to_user=to_user,
        family=family,
        progress='진행중'
    )

    return Response({"message": "가족 초대 요청이 전송되었습니다."}, status=status.HTTP_201_CREATED)

# 가족 초대 요청 상태 확인
@api_view(['GET'])
def check_invitation_status(request):
    requests = FamilyRequest.objects.filter(to_user=request.user)
    response_data = []
    for request in requests:
        response_data.append({
            'from_user': request.from_user.nickname,
            'family_id': request.family.family_id,
            'progress': request.progress,
        })
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def pending_family_request(request):
    """
    진행 중인 가족 초대 요청을 가져오는 API.
    로그인한 사용자에게 도착한 초대 요청이 있는지 확인합니다.
    """
    try:
        # 현재 사용자가 받은 초대 요청 중 진행중인 요청 가져오기
        pending_requests = FamilyRequest.objects.filter(to_user_id=request.user, progress='진행중')

        if not pending_requests.exists():
            print("????")
            return Response({"message": "진행중인 가족 초대 요청이 없습니다."}, status=status.HTTP_200_OK)

        # 여러 초대 요청 중 첫 번째 요청만 처리
        pending_request = pending_requests.first()
        serializer = FamilyRequestSerializer(pending_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 가족 초대 승인/거절
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_invitation(request):
    data = request.data
    family_request = get_object_or_404(FamilyRequest, id=data['request_id'])

    if data['action'] == '승인':
        # FamilyList에 추가
        FamilyList.objects.create(
            family=family_request.family,
            user=request.user
        )
        family_request.progress = '승인'
        family_request.save()
        return Response({"message": "가족 초대가 승인되었습니다.", "family_id": family_request.family.family_id}, status=status.HTTP_200_OK)
    elif data['action'] == '거절':
        family_request.progress = '거절'
        family_request.save()
        return Response({"message": "가족 초대가 거절되었습니다."}, status=status.HTTP_200_OK)

    return Response({"error": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Family

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_family(request, family_id):
    try:
        # 가족 객체 가져오기
        family = Family.objects.get(family_id=family_id)
    except Family.DoesNotExist:
        return Response({"error": "가족이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 요청자가 가족 삭제 권한이 있는지 확인
    if family.user != request.user:
        return Response({"error": "가족을 삭제할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    try:
        # 연결된 FamilyList 데이터 삭제
        FamilyList.objects.filter(family=family).delete()

        # 가족 삭제
        family.delete()

        # 삭제 성공 메시지 반환
        return Response({"message": "가족이 성공적으로 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        print(f"Error deleting family: {e}")
        return Response({"error": "가족 삭제 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def family_members(request):
    try:
        # 현재 사용자가 속한 가족의 구성원 가져오기
        family_members = FamilyList.objects.filter(
            family_user=request.user
        ).select_related('user')

        # 구성원을 직렬화
        serializer = UserSerializer(
            [member.user for member in family_members], many=True
        )
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response(
            {"error": str(e)}, status=500
        )

# 로그인된 사용자 정보 반환하는 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=200)


# 질문 db에 저장(gpt)
import json
import logging
logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt

# OpenAI API Key 설정
openai.api_key = 'OPENAI_API_KEY'
@csrf_exempt
def save_question(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question_text = data.get('question', '')

        # 데이터베이스에 질문 저장
        question = DailyQuestion.objects.create(question=question_text)
        return JsonResponse({'message': 'Question saved successfully!', 'id': question.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# 질문 가져오기
def question_list(request):
    questions = DailyQuestion.objects.all().values('id', 'question')
    return JsonResponse(list(questions), safe=False)


# 답변 저장하기
@csrf_exempt
@api_view(['POST'])
def save_answer(request):
    question_id = request.data.get('question_id')
    answer_text = request.data.get('answer')

    if not question_id or not answer_text:
        return Response({"error": "question_id and answer are required."}, status=status.HTTP_400_BAD_REQUEST)

    answer = Answer(question_id=question_id, answer=answer_text)
    answer.save()
    return Response({"message": "Answer saved successfully."}, status=status.HTTP_201_CREATED)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

# 회원탈퇴 API
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # 인증된 사용자만 접근 가능
def delete_account(request):
    user = request.user
    user.delete()  # 사용자 계정 삭제
    return Response(status=204)

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# 로그아웃
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "Refresh token not provided"}, status=400)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()  # refresh 토큰을 블랙리스트에 등록하여 무효화
        return Response({"message": "로그아웃 성공"}, status=205)
    except Exception as e:
        print(f"로그아웃 실패 - 예외 발생: {e}")
        return Response({"error": f"로그아웃 실패: {str(e)}"}, status=400)



#캘린더 이벤트 생성하기
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Event, Family
from .serializers import EventSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_event(request):
    serializer = EventSerializer(data=request.data)

    if serializer.is_valid():
        event = serializer.save()  # family_id 처리는 Serializer의 create 메서드에서 수행
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#캘린더 이벤트 가져오기
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_family_events(request):
    family_id = request.query_params.get('family_id')

    if not family_id:
        return Response({"error": "family_id parameter is required"}, status=400)

    events = Event.objects.filter(family_id=family_id)
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)




#캘린더 이벤트 삭제하기
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Event

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_event(request):
    try:
        # 요청에서 삭제할 기준 정보 받기
        user = request.user
        event_type = request.data.get('event_type')
        nickname = request.data.get('nickname')
        event_content = request.data.get('event_content')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # 사용자가 가족과 연결된 경우 해당 가족의 이벤트를 삭제 대상으로 설정
        family_list_entry = FamilyList.objects.filter(user=user).first()
        if family_list_entry:
            family = family_list_entry.family
            events = Event.objects.filter(
                family=family,
                event_type=event_type,
                nickname=nickname,
                event_content=event_content,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            # 가족이 없을 경우 개인 일정만 삭제
            events = Event.objects.filter(
                family__isnull=True,  # 개인 일정은 family가 null인 경우로 가정
                nickname=nickname,
                event_type=event_type,
                event_content=event_content,
                start_date=start_date,
                end_date=end_date,
            )

        if events.exists():
            deleted_count, _ = events.delete()
            return Response({"message": f"{deleted_count} events deleted successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No matching events found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#이벤트 업데이트
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Event
from .serializers import EventSerializer
from datetime import datetime

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_event(request):
    # 기존 이벤트 정보
    old_event_content = request.data.get('old_event_content')
    old_start_date = request.data.get('old_start_date')
    old_end_date = request.data.get('old_end_date')

    # 업데이트할 정보
    new_event_type = request.data.get('new_event_type')
    new_nickname = request.data.get('new_nickname')
    new_event_content = request.data.get('new_event_content')
    new_start_date = request.data.get('new_start_date')
    new_end_date = request.data.get('new_end_date')
    family_id = request.data.get('family_id')

    try:
        # 기존 이벤트 필터링
        event = Event.objects.filter(
            event_content=old_event_content,
            start_date=old_start_date,
            end_date=old_end_date,
            family_id=family_id
        ).first()

        if not event:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # 새 데이터로 업데이트
        event.event_type = new_event_type
        event.nickname = new_nickname
        event.event_content = new_event_content
        event.start_date = datetime.strptime(new_start_date, "%Y-%m-%d").date()
        event.end_date = datetime.strptime(new_end_date, "%Y-%m-%d").date()
        event.save()

        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#폰트 설정
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def font_setting(request):
    user = request.user
    if request.method == 'GET':
        setting, _ = UserFontSetting.objects.get_or_create(user=user)
        return Response({'font_size': setting.font_size})
    elif request.method == 'PUT':
        font_size = request.data.get('font_size')
        if font_size is not None:
            setting, _ = UserFontSetting.objects.get_or_create(user=user)
            setting.font_size = font_size
            setting.save()
            return Response({'message': 'Font size updated successfully'})
        return Response({'error': 'Invalid font size'}, status=400)