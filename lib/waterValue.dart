import 'package:flutter/material.dart';

class WaterValue extends StatefulWidget {
  String link;
  WaterValue({Key key, @required this.link}) : super(key: key);
  @override
  _WaterValue createState() => _WaterValue();
}

class _WaterValue extends State<WaterValue> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        child: Center(child: Text(widget.link.toString())),
      ),
    );
  }
}
