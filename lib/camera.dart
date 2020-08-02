import 'package:flutter/material.dart';
import 'package:sensors/sensors.dart';
import 'package:camera/camera.dart';

import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' show join;

import 'dart:io';
import 'dart:convert';
import 'package:sih/waterValue.dart';

List<CameraDescription> cameras;

class Home extends StatefulWidget {
  @override
  _HomeState createState() => _HomeState();
}

class _HomeState extends State<Home> {
  AccelerometerEvent event;
  CameraController controller;
  Map<dynamic, dynamic> temp;

  double lat, long;
  bool clicked = false;

  void cameraGet() async {
    cameras = await availableCameras();
    controller = CameraController(cameras[0], ResolutionPreset.medium);
    controller.initialize().then((_) {
      if (!mounted) {
        return;
      }
      setState(() {});
    });
  }

  @override
  void initState() {
    cameraGet();
    super.initState();
  }

  @override
  void dispose() {
    controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        child: Stack(
          children: [
            !controller.value.isInitialized
                ? Container()
                : AspectRatio(
                    aspectRatio: controller.value.aspectRatio,
                    child: CameraPreview(controller)),
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  IconButton(
                      icon: Icon(
                        Icons.camera_alt,
                        size: 40.0,
                        color: Colors.black,
                      ),
                      onPressed: () {
                        _onCapturePressed(context);
                      }),
                  SizedBox(
                    height: 30.0,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _onCapturePressed(context) async {
    try {
      // 1
      final path = join(
        (await getTemporaryDirectory()).path,
        '${DateTime.now()}.png',
      );
      // 2
      await controller.takePicture(path);
      final bytes = File(path).readAsBytesSync();
      dynamic a = base64Encode(bytes);
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => WaterValue(img: a),
        ),
      );
      // 3
    } catch (e) {
      print(e);
    }
  }
}
