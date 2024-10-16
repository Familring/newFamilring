import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'question_notification.dart'; // QuestionNotification 파일 임포트

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // bool _hasNavigated = false;  // 화면 전환 여부를 저장할 플래그

  @override
  void initState() {
    super.initState();
    // _checkFirstVisit();
    Future.delayed(Duration(seconds: 1), () {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => QuestionNotification()),
      );
    });
  }

  // 첫 방문인지 체크하는 함수
  // Future<void> _checkFirstVisit() async {
  //   SharedPreferences prefs = await SharedPreferences.getInstance();
  //   bool? hasNavigated = prefs.getBool('hasNavigated') ?? false;
  //
  //   if (!hasNavigated) {
  //     // 첫 방문일 때 1초 뒤에 QuestionNotification으로 화면 전환
  //     Future.delayed(Duration(seconds: 1), () {
  //       Navigator.push(
  //         context,
  //         MaterialPageRoute(builder: (context) => QuestionNotification()),
  //       );
  //     });
  //     // 첫 방문 이후에 hasNavigated 값을 true로 설정
  //     await prefs.setBool('hasNavigated', true);
  //   }
  // }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Padding(
          padding: const EdgeInsets.only(left: 18.0, top: 10.0), // 위쪽 여백 추가
          child: SizedBox(
            width: 42, // 이미지 크기 조정
            height: 42,
            child: Image.asset(
              'images/appbaricon.png', // 이미지 파일 경로
              fit: BoxFit.contain,
            ),
          ),
        ),
      ),
      body: Center(
        child: Text(
          '환영합니당',
          style: TextStyle(fontSize: 24),
        ),
      ),
    );
  }
}
