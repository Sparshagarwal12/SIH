import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:sih/sun/click.dart';
import 'package:sih/water/select.dart';
import 'package:geolocator/geolocator.dart';

class SelectTurbid extends StatefulWidget {
  @override
  _SelectTurbid createState() => _SelectTurbid();
}

class _SelectTurbid extends State<SelectTurbid> {
  Position _currentPosition;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
          child: Center(
              child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          GestureDetector(
            onTap: () {
              Navigator.push(context,
                  CupertinoPageRoute(builder: (context) => SunClick()));
            },
            child: Container(
              height: MediaQuery.of(context).size.height / 3,
              width: MediaQuery.of(context).size.width / 1.5,
              decoration: BoxDecoration(
                  color: Colors.pink,
                  borderRadius: BorderRadius.circular(40),
                  boxShadow: [
                    BoxShadow(
                        color: Colors.grey.shade400,
                        offset: Offset(5, 5),
                        blurRadius: 5.0,
                        spreadRadius: 1.0)
                  ]),
              child: Center(
                  child: Text(
                "Sun Turbidity",
                style: TextStyle(fontSize: 30, color: Colors.white),
              )),
            ),
          ),
          SizedBox(height: 30),
          GestureDetector(
            onTap: () async {
              await _getCurrentLocation();
              if (_currentPosition.latitude != null &&
                  _currentPosition.longitude != null) {
                Navigator.push(
                    context,
                    CupertinoPageRoute(
                        builder: (context) => SelectType(
                              lat: _currentPosition.latitude,
                              long: _currentPosition.longitude,
                            )));
              } else {
                print('bbud');
              }
            },
            child: Container(
              height: MediaQuery.of(context).size.height / 3,
              width: MediaQuery.of(context).size.width / 1.5,
              decoration: BoxDecoration(
                  color: Colors.pink,
                  borderRadius: BorderRadius.circular(40),
                  boxShadow: [
                    BoxShadow(
                        color: Colors.grey.shade400,
                        offset: Offset(5, 5),
                        blurRadius: 5.0,
                        spreadRadius: 1.0)
                  ]),
              child: Center(
                  child: Text(
                "Water Turbidity",
                style: TextStyle(fontSize: 30, color: Colors.white),
              )),
            ),
          ),
        ],
      ))),
    );
  }

  _getCurrentLocation() {
    final Geolocator geolocator = Geolocator()..forceAndroidLocationManager;

    geolocator
        .getCurrentPosition(desiredAccuracy: LocationAccuracy.best)
        .then((Position position) {
      setState(() {
        _currentPosition = position;
      });
    }).catchError((e) {
      print(e);
    });
  }
}
