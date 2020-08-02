import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'dart:convert';

import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' show join;
import 'package:camera/camera.dart';
import 'package:sensors/sensors.dart';

import 'package:firebase_storage/firebase_storage.dart';

List<CameraDescription> cameras;

class SelectType extends StatefulWidget {
  dynamic lat;
  dynamic long;
  SelectType({Key key, @required this.lat, @required this.long})
      : super(key: key);
  @override
  _SelectType createState() => _SelectType();
}

class _SelectType extends State<SelectType> {
  bool clicked = false;

  Map<dynamic, dynamic> temp;
  // void getAngle() async {
  //   // checkLocationpermission();
  //   String url = "http://ec2-52-71-253-148.compute-1.amazonaws.com/sun";
  //   http.Response response = await http.post(url,
  //       headers: <String, String>{
  //         'Content-Type': 'application/json; charset=UTF-8',
  //       },
  //       body: json.encode(<String, double>{
  //         "latitude": widget.lat,
  //         "longitude": widget.long
  //       }));
  //   temp = json.decode(response.body);
  //   setState(() {
  //     clicked = true;
  //   });
  // }

  AccelerometerEvent event;
  CameraController controller;
  File cameraFile;
  File f1;
  File f2;
  File f3;

  // String getY() {
  //   return ((event.y * 90) / 10).ceilToDouble().toString();
  // }

  // String getZ() {
  //   return ((event.z * 90) / 10).ceilToDouble().toString();
  // }
  _imageSelect(ImageSource source, String val) async {
    cameraFile = await ImagePicker.pickImage(source: source);
    setState(() {
      if (val == "a") {
        f1 = cameraFile;
      } else if (val == "b") {
        f2 = cameraFile;
      } else if (val == "c") {
        f3 = cameraFile;
      }
    });
  }

  // Future uploadPic(BuildContext context, File _image) async {
  //   String fileName = _image.path;
  //   StorageReference firebaseStorageRef =
  //       FirebaseStorage.instance.ref().child(fileName);
  //   StorageUploadTask uploadTask = firebaseStorageRef.putFile(_image);
  //   StorageTaskSnapshot taskSnapshot = await uploadTask.onComplete;
  //   final String url = await firebaseStorageRef.getDownloadURL();

  //   print(url);
  //   setState(() {
  //     apiCall(url);
  //   });
  // }

  dynamic mod;
  // apiCall(String uri) async {
  //   String url = 'http://ec2-52-71-253-148.compute-1.amazonaws.com/water';
  //   var body = {"imageurl": uri};
  //   http.Response r = await http.post(
  //     Uri.parse(url),
  //     headers: {"Content-Type": "application/json"},
  //     body: json.encode(body),
  //   );
  //   print(r.body);
  // setState(() {
  //   mod = json.decode(r.body);
  // });
  //   print(mod["message"]);
  // }

  turbidity(String a, String b, String c) async {
    String url = 'http://ec2-52-71-253-148.compute-1.amazonaws.com/turbidity';
    var body = {"skyImge": a, "waterImage": b, "greyImage": c};
    http.Response r = await http.post(
      Uri.parse(url),
      headers: {"Content-Type": "application/json"},
      body: json.encode(body),
    );
    print(r.body);
    setState(() {
      mod = json.decode(r.body);
    });
  }

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

  // @override
  // void initState() {
  //   cameraGet();
  //   super.initState();
  // }

  // @override
  // void dispose() {
  //   controller?.dispose();
  //   super.dispose();
  // }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
          child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: <Widget>[
          SizedBox(height: 40),
          Column(
            children: <Widget>[
              Row(
                children: <Widget>[
                  f1 == null
                      ? Padding(
                          padding: EdgeInsets.all(10),
                          child: GestureDetector(
                              onTap: () {
                                showDialog(
                                  context: context,
                                  builder: (BuildContext context) {
                                    return AlertDialog(
                                      title: Text("Select Source"),
                                      content: Container(
                                          child: Stack(
                                        children: <Widget>[
                                          GestureDetector(
                                              onTap: () {
                                                _imageSelect(
                                                    ImageSource.gallery, "a");
                                              },
                                              child: Text("Gallery")),
                                          Padding(
                                              padding: EdgeInsets.only(top: 40),
                                              child: GestureDetector(
                                                  onTap: () {
                                                    _imageSelect(
                                                        ImageSource.gallery,
                                                        "a");
                                                  },
                                                  child: Text("Camera")))
                                        ],
                                      )),
                                    );
                                  },
                                );
                              },
                              child: Container(
                                height: MediaQuery.of(context).size.height / 4,
                                width: MediaQuery.of(context).size.width / 2.4,
                                decoration: BoxDecoration(
                                    color: Colors.pink,
                                    borderRadius: BorderRadius.circular(10),
                                    boxShadow: [
                                      BoxShadow(
                                          color: Colors.grey.shade400,
                                          offset: Offset(5, 5),
                                          blurRadius: 5.0,
                                          spreadRadius: 1.0)
                                    ]),
                                child: Center(
                                    child: Text(
                                  "Gray Card",
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                      fontSize: 30, color: Colors.white),
                                )),
                              )))
                      : Padding(
                          padding: EdgeInsets.all(10),
                          child: Container(
                            height: MediaQuery.of(context).size.height / 4,
                            width: MediaQuery.of(context).size.width / 2.4,
                            decoration: BoxDecoration(
                              image: DecorationImage(image: FileImage(f1)),
                              borderRadius: BorderRadius.circular(10),
                              // boxShadow: [
                              //   BoxShadow(
                              //       color: Colors.grey.shade400,
                              //       offset: Offset(5, 5),
                              //       blurRadius: 5.0,
                              //       spreadRadius: 1.0)
                              // ]
                            ),
                          )),
                  f2 == null
                      ? Padding(
                          padding: EdgeInsets.all(10),
                          child: GestureDetector(
                              onTap: () {
                                showDialog(
                                  context: context,
                                  builder: (BuildContext context) {
                                    return AlertDialog(
                                      title: Text("Select Source"),
                                      content: Container(
                                          child: Stack(
                                        children: <Widget>[
                                          GestureDetector(
                                              onTap: () {
                                                _imageSelect(
                                                    ImageSource.gallery, "b");
                                              },
                                              child: Text("Gallery")),
                                          Padding(
                                              padding: EdgeInsets.only(top: 40),
                                              child: GestureDetector(
                                                  onTap: () {
                                                    _imageSelect(
                                                        ImageSource.gallery,
                                                        "b");
                                                  },
                                                  child: Text("Camera")))
                                        ],
                                      )),
                                    );
                                  },
                                );
                                // cam("b");
                              },
                              child: Container(
                                height: MediaQuery.of(context).size.height / 4,
                                width: MediaQuery.of(context).size.width / 2.4,
                                decoration: BoxDecoration(
                                    color: Colors.pink,
                                    borderRadius: BorderRadius.circular(10),
                                    boxShadow: [
                                      BoxShadow(
                                          color: Colors.grey.shade400,
                                          offset: Offset(5, 5),
                                          blurRadius: 5.0,
                                          spreadRadius: 1.0)
                                    ]),
                                child: Center(
                                    child: Text(
                                  "Water",
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                      fontSize: 30, color: Colors.white),
                                )),
                              )))
                      : Padding(
                          padding: EdgeInsets.all(10),
                          child: Container(
                            height: MediaQuery.of(context).size.height / 4,
                            width: MediaQuery.of(context).size.width / 2.4,
                            decoration: BoxDecoration(
                              image: DecorationImage(image: FileImage(f2)),
                              borderRadius: BorderRadius.circular(10),
                              // boxShadow: [
                              //   BoxShadow(
                              //       color: Colors.grey.shade400,
                              //       offset: Offset(5, 5),
                              //       blurRadius: 5.0,
                              //       spreadRadius: 1.0)
                              // ]
                            ),
                          )),
                ],
              ),
              f3 == null
                  ? Padding(
                      padding: EdgeInsets.all(10),
                      child: GestureDetector(
                          onTap: () {
                            showDialog(
                                  context: context,
                                  builder: (BuildContext context) {
                                    return AlertDialog(
                                      title: Text("Select Source"),
                                      content: Container(
                                          child: Stack(
                                        children: <Widget>[
                                          GestureDetector(
                                              onTap: () {
                                                _imageSelect(
                                                    ImageSource.gallery, "c");
                                              },
                                              child: Text("Gallery")),
                                          Padding(
                                              padding: EdgeInsets.only(top: 40),
                                              child: GestureDetector(
                                                  onTap: () {
                                                    _imageSelect(
                                                        ImageSource.gallery,
                                                        "c");
                                                  },
                                                  child: Text("Camera")))
                                        ],
                                      )),
                                    );
                                  },
                                );
                            // cam("c");
                          },
                          child: Container(
                            height: MediaQuery.of(context).size.height / 4,
                            width: MediaQuery.of(context).size.width / 2,
                            decoration: BoxDecoration(
                                color: Colors.pink,
                                borderRadius: BorderRadius.circular(10),
                                boxShadow: [
                                  BoxShadow(
                                      color: Colors.grey.shade400,
                                      offset: Offset(5, 5),
                                      blurRadius: 5.0,
                                      spreadRadius: 1.0)
                                ]),
                            child: Center(
                                child: Text(
                              "Sun",
                              textAlign: TextAlign.center,
                              style:
                                  TextStyle(fontSize: 30, color: Colors.white),
                            )),
                          )))
                  : Padding(
                      padding: EdgeInsets.all(10),
                      child: Container(
                        height: MediaQuery.of(context).size.height / 4,
                        width: MediaQuery.of(context).size.width / 2.4,
                        decoration: BoxDecoration(
                          image: DecorationImage(image: FileImage(f3)),
                          borderRadius: BorderRadius.circular(10),
                          // boxShadow: [
                          //   BoxShadow(
                          //       color: Colors.grey.shade400,
                          //       offset: Offset(5, 5),
                          //       blurRadius: 5.0,
                          //       spreadRadius: 1.0)
                          // ]
                        ),
                      )),
            ],
          ),
          SizedBox(height: 30),
          Column(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: <Widget>[
              Text(
                "Latitude:  " + widget.lat.toString(),
                style: TextStyle(
                  fontSize: 30,
                ),
              ),
              SizedBox(height: 5),
              Text(
                "Longitude:  " + widget.long.toString(),
                style: TextStyle(
                  fontSize: 30,
                ),
              ),
            ],
          ),
          SizedBox(height: 50),
          f1 != null && f2 != null && f3 != null
              ? Container(
                  width: MediaQuery.of(context).size.width / 2,
                  decoration: BoxDecoration(
                      color: Colors.blue,
                      borderRadius: BorderRadius.circular(30)),
                  child: FlatButton(
                      onPressed: () async {
                        showDialog(
                          context: context,
                          builder: (BuildContext context) {
                            return AlertDialog(
                                backgroundColor: Colors.transparent,
                                elevation: 0,
                                content:
                                    Center(child: CircularProgressIndicator()));
                          },
                        );
                        final bytes = File(f1.path).readAsBytesSync();
                        String a = base64Encode(bytes);

                        final bytes2 = File(f2.path).readAsBytesSync();
                        String b = base64Encode(bytes2);

                        final bytes3 = File(f3.path).readAsBytesSync();
                        String c = base64Encode(bytes3);
                        await turbidity(a, b, c);
                        // await apiCall(b);

                        // showDialog(
                        //   context: context,
                        //   builder: (BuildContext context) {
                        //     Widget continueButton = FlatButton(
                        //       child: Text("Ok"),
                        //       onPressed: () {
                        //         Navigator.pop(context);
                        //       },
                        //     );
                        //     return AlertDialog(
                        //       title: Text("Turbidity Value"),
                        //       content: Text(mod["message"].toString()),
                        //       actions: [
                        //         continueButton,
                        //       ],
                        //     );
                        //   },
                        // );
                      },
                      child: Text(
                        "Submit",
                        style: TextStyle(fontSize: 20),
                      )))
              : Container(
                  child: Text(
                  "Please Select All 3 Images",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
                ))
        ],
      )),
    );
  }

  // Widget cam(String val) {
  //   return Scaffold(
  //     body: Container(
  //       child: Stack(
  //         children: [
  //           !controller.value.isInitialized
  //               ? Container()
  //               : AspectRatio(
  //                   aspectRatio: controller.value.aspectRatio,
  //                   child: CameraPreview(controller)),
  //           Center(
  //             child: Column(
  //               mainAxisAlignment: MainAxisAlignment.end,
  //               children: [
  //                 GestureDetector(
  //                   onTap: () {
  //                     getAngle();
  //                   },
  //                   child: Text(
  //                     !clicked
  //                         ? "press"
  //                         : "zenith: " +
  //                             temp["zenith"].toString() +
  //                             "\nazimuth: " +
  //                             temp["azimuth"].toString() +
  //                             "\nelevation: " +
  //                             temp["altitude"].toString(),
  //                     style: TextStyle(color: Colors.black, fontSize: 15.0),
  //                   ),
  //                 ),
  //                 SizedBox(
  //                   height: 20.0,
  //                 ),
  //                 GestureDetector(
  //                     onTap: () {
  //                       accelerometerEvents.listen((AccelerometerEvent eve) {
  //                         // print(eve.y * 90 / 10);
  //                         setState(() {
  //                           event = eve;
  //                         });
  //                       });
  //                     },
  //                     child: Text(
  //                       event == null ? "Press" : "Y: " + getY(),
  //                       style: TextStyle(color: Colors.black, fontSize: 15.0),
  //                     )),
  //                 SizedBox(
  //                   height: 20.0,
  //                 ),
  //                 IconButton(
  //                     icon: Icon(
  //                       Icons.camera_alt,
  //                       size: 40.0,
  //                       color: Colors.black,
  //                     ),
  //                     onPressed: () async {
  //                       try {
  //                         final path = join(
  //                           (await getTemporaryDirectory()).path,
  //                           '${DateTime.now()}.png',
  //                         );
  //                         await controller.takePicture(path);
  //                         setState(() {
  //                           if (val == "a") {
  //                             f1 = cameraFile;
  //                           } else if (val == "b") {
  //                             f2 = cameraFile;
  //                           } else if (val == "c") {
  //                             f3 = cameraFile;
  //                           }
  //                         });
  //                       } catch (e) {
  //                         print(e);
  //                       }
  //                     }),
  //                 SizedBox(
  //                   height: 30.0,
  //                 ),
  //               ],
  //             ),
  //           ),
  //         ],
  //       ),
  //     ),
  //   );
  // }
}
