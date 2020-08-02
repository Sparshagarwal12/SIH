import 'package:flutter/material.dart';
import 'dart:io';
import 'dart:convert';

class WaterValue extends StatefulWidget {
  dynamic img;
  WaterValue({Key key, @required this.img}) : super(key: key);
  @override
  _WaterValue createState() => _WaterValue();
}

class _WaterValue extends State<WaterValue> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        height: 300,
        width: 300,
        decoration: BoxDecoration(
            image:
                DecorationImage(image: MemoryImage(base64Decode(widget.img)))),
      ),
    );
  }
}
