'use strict';

var CTRL_LOADED = 'background: lime; color: #181818';


angular.module('sven.controllers', ['angularFileUpload'])
  /*
    
    The very main controller. Handle django orm filters in ng-view .
    ===
    
    limit and offset of the curtrent view are also set.
  */
  .controller('layoutCtrl', ['$scope', '$rootScope','$location', '$route', function($scope, $rootScope, $location, $route) {

    $scope.limit = 25;
    $scope.offset= 0;
    $scope.filters = {};
    $scope.query = {};
    
    console.log('%c layoutCtrl ', CTRL_LOADED);
    
    // look after the current corpus, babe.
    $rootScope.corpus = {};
  

    $scope.paginate = function(options) {
      var options = options || {},
          pages = [],
          left = 0,
          right = 0;

      $scope.total_count = options.total_count;
      
      
      $scope.numofpages = Math.floor($scope.total_count / $scope.limit );
      $scope.page = Math.floor($scope.offset / $scope.limit);

      if($scope.numofpages < 10) {
        left = 0;
        right = +$scope.numofpages;
      } else{
        right = Math.min($scope.numofpages, $scope.page<10?10:$scope.page + 5);
        left = right - 10;
      }

      for(var i=left; i<right+1; i++)
        pages.push(i+1);

      $scope.pages = pages;
      console.log('$scope.paginate', pages);
    }
  }])
  .controller('indexCtrl', ['$scope', function() {


  }])
  /*

    Sidebar user corpora ctrl.
    ===
  */
  .controller('corpusListCtrl', ['$scope', 'CorpusListFactory', function($scope, CorpusListFactory) {
    
    $scope.sync = function() {
      CorpusListFactory.query(function(data){
        $scope.items = data.objects;
      });
    };
    
    $scope.sync();
    console.log('%c corpusListCtrl ', CTRL_LOADED);
  }])
  /*

    Sidebar user corpora ctrl.
    ===
  */
  .controller('documentListCtrl', ['$scope', '$upload', '$routeParams', 'DocumentListFactory', function($scope, $upload, $routeParams, DocumentListFactory) {
    
    $scope.sync = function() {
      DocumentListFactory.query({id: $routeParams.id, limit:$scope.limit, offset:$scope.offset, filters:$scope.filters}, function(data){
          console.log(data);
          $scope.items = data.objects;
          $scope.paginate({
            total_count: data.meta.total_count
          });
      });
    };

    $scope.uploadprogress = 100;

    $scope.onFileSelect = function($files) {
      for (var i = 0; i < $files.length; i++) {
        var file = $files[i];
        $scope.upload = $upload.upload({
          url: '/api/corpus/' + $routeParams.id + '/upload', //upload.php script, node.js route, or servlet url
          // method: POST or PUT,
          // headers: {'headerKey': 'headerValue'},
          // withCredentials: true,
          data: {myObj: $scope.myModelObj},
          file: file,
          // file: $files, //upload multiple files, this feature only works in HTML5 FromData browsers
          /* set file formData name for 'Content-Desposition' header. Default: 'file' */
          //fileFormDataName: myFile, //OR for HTML5 multiple upload only a list: ['name1', 'name2', ...]
          /* customize how data is added to formData. See #40#issuecomment-28612000 for example */
          //formDataAppender: function(formData, key, val){} //#40#issuecomment-28612000
        }).progress(function(evt) {
          $scope.uploadprogress = parseInt(100.0 * evt.loaded / evt.total)
          console.log('percent: ' + $scope.uploadprogress);
        }).success(function(data, status, headers, config) {
          // file is uploaded successfully
          console.log(data);
          $scope.uploadprogress = 100;
          $scope.sync();
        });
        //.error(...)
        //.then(success, error, progress); 
      }
    // $scope.upload = $upload.upload({...}) alternative way of uploading, sends the the file content directly with the same content-type of the file. Could be used to upload files to CouchDB, imgur, etc... for HTML5 FileReader browsers. 
    };

    $scope.sync();
    console.log('%c documentListCtrl ', CTRL_LOADED);
  }])
  .controller('documentCtrl', ['$scope', '$routeParams', 'DocumentFactory', 'DocumentSegmentsFactory', function($scope, $routeParams, DocumentFactory, DocumentSegmentsFactory) {
    DocumentFactory.query({id: $routeParams.id}, function(data){
      $scope.item = data.object;
      
      DocumentSegmentsFactory.query({id: $routeParams.id}, function(data){
        console.log(data);
        $scope.segments = data.objects
      })
    });

  }])
  .controller('contextCtrl', ['$scope', function($scope) {


  }])
  .controller('blankCtrl', ['$scope', function($scope) {


  }])