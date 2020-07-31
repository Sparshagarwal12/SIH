import 'dart:typed_data';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'dart:io';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:sih/waterValue.dart';

class Picker extends StatefulWidget {
  @override
  _Picker createState() => _Picker();
}

class _Picker extends State<Picker> {
  String link;

  List<dynamic> imageData = [];
  Future uploadPic(BuildContext context, File _image) async {
    String fileName = _image.path;
    StorageReference firebaseStorageRef =
        FirebaseStorage.instance.ref().child(fileName);
    StorageUploadTask uploadTask = firebaseStorageRef.putFile(_image);
    StorageTaskSnapshot taskSnapshot = await uploadTask.onComplete;
    final String url = await firebaseStorageRef.getDownloadURL();

    print(url);
    setState(() {
      // val = true;
      link = url.toString();
      apiCall(link);
    });
  }

  String _imagePath = 'Unknown';
  @override
  void initState() {
    super.initState();
  }

  bool val = false;
  File galleryFile;
  File cameraFile;
  dynamic bytes;
  imageSelectorGallery() async {
    galleryFile = await ImagePicker.pickImage(
      source: ImageSource.gallery,
    );

    File croppedFile = await ImageCropper.cropImage(
      sourcePath: galleryFile.path,
      androidUiSettings: AndroidUiSettings(
          toolbarTitle: 'Scan Karo',
          toolbarColor: Color(0xFF007f5f),
          toolbarWidgetColor: Colors.white,
          initAspectRatio: CropAspectRatioPreset.original,
          lockAspectRatio: false),
    );
    setState(() {
      val = true;
    });
    uploadPic(context, croppedFile);
  }

  imageSelectorCamera() async {
    cameraFile = await ImagePicker.pickImage(
      source: ImageSource.camera,
    );
    setState(() {});
    File croppedFile = await ImageCropper.cropImage(
      cropStyle: CropStyle.rectangle,
      sourcePath: cameraFile.path,
      androidUiSettings: AndroidUiSettings(
          toolbarTitle: 'SIH',
          toolbarColor: Color(0xFF007f5f),
          toolbarWidgetColor: Colors.white,
          initAspectRatio: CropAspectRatioPreset.original,
          lockAspectRatio: false),
    );

    uploadPic(context, croppedFile);
  }

  void apiCall(String uri) async {
    String url = 'http://ec2-52-71-253-148.compute-1.amazonaws.com';
    var body = {"imageurl": uri};
    http.Response r = await http.post(
      Uri.parse(url),
      headers: {"Content-Type": "application/json"},
      body: json.encode(body),
    );
    print(r.body);
    Navigator.push(
        context,
        MaterialPageRoute(
            builder: (context) => WaterValue(
                  link: r.body,
                )));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: val
          ? FloatingActionButton(
              backgroundColor: Color(0xFF007f5f),
              onPressed: () {
                apiCall(link);
              },
              child: Icon(Icons.cloud_upload),
            )
          : FloatingActionButton(
              backgroundColor: Color(0xFF007f5f),
              onPressed: () {
                imageSelectorCamera();
              },
              child: Icon(Icons.camera),
            ),
      body: Container(
        height: MediaQuery.of(context).size.height,
        child: val
            ? Center(
                child: CircularProgressIndicator(),
              )
            : GestureDetector(
                onTap: () {
                  imageSelectorGallery();
                },
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Center(
                        child: Image.asset(
                      'assets/upload.png',
                      width: MediaQuery.of(context).size.width,
                      fit: BoxFit.contain,
                    )),
                    Center(
                      child: Text("Tap To Select Image",
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.black,
                            fontSize: 30,
                          )),
                    )
                  ],
                )),
      ),
    );
  }
}
