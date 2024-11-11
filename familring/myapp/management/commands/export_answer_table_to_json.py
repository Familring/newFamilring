import os
import json
from django.core.management.base import BaseCommand
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

class Command(BaseCommand):
    help = "Load JSON file, split text, embed, and save to Chroma vector store"

    def handle(self, *args, **kwargs):
        # JSON 파일 경로 설정
        json_file_path = "family_22_answers.json"
        self.stdout.write(f"{json_file_path}에서 JSON 파일 로드 중...")

        # JSON 파일을 직접 로드하여 리스트 형식으로 가져오기
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.stdout.write(f"JSON 파일 로드 완료. 데이터 개수: {len(data)}")
        except Exception as e:
            self.stdout.write(f"JSON 파일 로드 중 오류 발생: {e}")
            return

        # 데이터를 Document 객체 리스트로 변환
        try:
            # data가 리스트인지 확인
            if isinstance(data, list):
                documents = [Document(page_content=item["answer"]) for item in data if "answer" in item]
                self.stdout.write(f"Document 객체로 변환 완료. 변환된 문서 개수: {len(documents)}")
            else:
                self.stdout.write("데이터가 리스트 형식이 아닙니다. JSON 파일의 구조를 확인하세요.")
                return
        except KeyError as e:
            self.stdout.write(f"데이터 변환 중 오류 발생 (KeyError): {e}")
            return

        # 텍스트 분할
        try:
            text_splitter = CharacterTextSplitter(chunk_size=250, chunk_overlap=50)
            split_docs = text_splitter.split_documents(documents)
            self.stdout.write(f"텍스트 분할 완료. 분할된 청크 수: {len(split_docs)}")
            for i, chunk in enumerate(split_docs[:5]):  # 처음 5개 청크만 출력
                self.stdout.write(f"청크 {i + 1}: {chunk.page_content[:100]}...")  # 일부만 출력
        except Exception as e:
            self.stdout.write(f"텍스트 분할 중 오류 발생: {e}")
            return

        # 임베딩 생성 및 벡터 저장
        try:
            embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
            vector_store = Chroma.from_documents(
                split_docs, embedding, collection_name="family_answers"
            )
            self.stdout.write(f"임베딩 생성 및 Chroma 벡터 저장소 저장 완료. 저장된 문서 수: {vector_store._collection.count()}")
        except Exception as e:
            self.stdout.write(f"임베딩 생성 또는 벡터 저장소 저장 중 오류 발생: {e}")
