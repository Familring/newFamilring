import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
//import 'package:openai_client/openai_client.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:async'; //타이머 패키지


class TodayQuestion extends StatefulWidget {
  @override
  _TodayQuestionState createState() => _TodayQuestionState();
}

class _TodayQuestionState extends State<TodayQuestion> {
  String question = "...Loading?"; // 질문
  String answer = ""; // 답변
  Timer? _timer;
  Duration interval = Duration(minutes:3);

  @override
  void initState() {
    super.initState();
    _openAi();
    _startQuestionGeneration();//질문 생성 시작
  }

  // 주기적으로 질문을 생성하는 함수
  void _startQuestionGeneration() {
    // 처음 질문을 즉시 생성
    _openAi();

    // 설정한 주기마다 질문을 생성
    _timer = Timer.periodic(interval, (Timer timer) {
      _openAi();

    }) as Timer?;
  }

  @override
  void dispose() {
    _timer?.cancel(); // 위젯이 제거될 때 타이머를 중지
    super.dispose();
  }


Future<void> _openAi() async {
    final apiKey = dotenv.env['OPENAI_API_KEY']!;
    final response = await http.post(
      Uri.parse('https://api.openai.com/v1/chat/completions'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $apiKey',
      },
      body: jsonEncode({
        'model': 'gpt-3.5-turbo',
        'messages': [
          {'role': 'system', 'content': 'Ask your users short, thought-provoking questions in korean. just create one question'},
          // {'role': 'user', 'content': 'What is Seoul?'}
        ],
        'max_tokens': 100,
      }),
    );

    if (response.statusCode == 200) {
      var data = jsonDecode(utf8.decode(response.bodyBytes)); //한국어로 변경
      setState(() {
        question = data['choices'][0]['message']['content'];
        print('API sucess: $question'); // 로그 추가
      });
      await _saveQuestionToDB(question);
    } else {
      setState(() {
        question = 'Error: ${response.reasonPhrase}';
        print('API fail: ${response.reasonPhrase}'); // 로그 추가
      });
    }
  }


  Future<void> _saveQuestionToDB(String question) async {
    final response = await http.post(
      Uri.parse('http://127.0.0.1:8000/api/save_question/'), // Django 서버 URL로 변경
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'question': question}),
    );

    if (response.statusCode == 200) {
      var data = jsonDecode(response.body);
      print('Question saved successfully with ID: ${data['id']}');
    } else {
      print('Failed to save question: ${response.reasonPhrase}');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('#두 번째 질문'),
        backgroundColor: Colors.white,
        elevation: 0, // 앱바의 그림자를 제거
        iconTheme: IconThemeData(
          color: Colors.black, // 앱바 아이콘 색상
        ),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            Text(
              'Q. $question',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              textAlign: TextAlign.left,
            ),
            SizedBox(height: 40),
            Text(
              'A.',
              style: TextStyle(fontSize: 18),
              textAlign: TextAlign.left,
            ),
            SizedBox(height: 10),
            TextField(
              onChanged: (text) {
                setState(() {
                  answer = text;
                });
              },
              maxLines: 10,
              decoration: InputDecoration(
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8.0),
                  borderSide: BorderSide(color: Color.fromARGB(255, 255, 207, 102)),
                ),
              ),
            ),
            SizedBox(height: 40),
            ElevatedButton(
              onPressed: () {
                // 답변 저장 로직 추가 가능
                // 예: 서버로 전송 또는 로컬 저장
                print('Question: $question');
                print('Answer: $answer');


                // 알림을 표시하고 TodayQuestion과 QuestionNotification 화면을 pop하여 HomeScreen으로 전환
                showDialog(
                  context: context,
                  builder: (BuildContext context) {
                    return AlertDialog(
                      title: Text('알림'),
                      content: Text('답변이 등록되었습니다.'),
                      actions: [
                        TextButton(
                          onPressed: () {
                            Navigator.of(context).pop(); // 다이얼로그 닫기
                            Navigator.pushNamedAndRemoveUntil(context, '/home', (route)=>false); // HomeScreen으로 돌아가기
                          },
                          child: Text('확인'),
                        ),
                      ],
                    );
                  },
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Color.fromARGB(255, 255, 207, 102), // 버튼 색상
                padding: EdgeInsets.symmetric(horizontal: 50, vertical: 15),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              child: Text(
                '답변 등록하기',
                style: TextStyle(fontSize: 16, color: Colors.white),
              ),
            ),


          ],

        ),
      ),
    );
  }
}
