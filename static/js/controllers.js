'use strict';

var CONTROLLER_STATUS_AVAILABLE = 'available',
    CONTROLLER_STATUS_WORKING = 'busy';

/* Controllers */

angular.module('sven.controllers', ['angularFileUpload'])
  /*

    Contains shared jquery plugin, like window-related plugin (toastmessage)
    ===
    
    Handle with care, and try not to override them locally.
  */
  .controller('initCtrl', ['$rootScope', function($rootScope) {
    $rootScope.toast = function(options){
      var options = options || {},
          settings = $.extend({
            text: "<div>"+(!options.title?"<h1>"+options.message+"</h1>":"<h1>"+options.title+"</h1><p>"+options.message+"</p>")+"</div>",
            type: "notice",
            position: "bottom-right",
            inEffectDuration: 200,
            outEffectDuration: 200,
            stayTime: 1900
          }, options);
      
      if(settings.cleanup != undefined)
        $().toastmessage("cleanToast");
      
      $().toastmessage("showToast", settings);
    };

    $rootScope.toast({message:"welcome to sven", stayTime: 3000000});
  }])

  /*

    Handle the main view. Unused
    ===
  
  */
  .controller('indexCtrl', ['$scope', function($scope) {
    
  }])
  /*
    
    System status controller
    ====

  */
  .controller('notificationCtrl', ['$rootScope', 'NotificationFactory', '$timeout', function($rootScope, NotificationFactory, $timeout) {
    console.log('load notificationCtrl')
    $rootScope.notification = {};
    $rootScope.activity = '.';
    // ugly ajax polling...
    (function tick() {
        $rootScope.activity = '..';

        NotificationFactory.query(function(data){
          $rootScope.activity = '...';
          $rootScope.notification = data;
          $timeout(tick, 2617);
        });
    })();

  }])
  /*
    
    System log controller (cfr. notificationCtrl)
    ====

  */
  .controller('logCtrl', ['$rootScope', '$scope', function($rootScope, $scope){

  }])
  /*

    Handle the profile view.
    ===
  
  */
  .controller('profileCtrl', ['$scope', 'ProfileFactory', function($scope, ProfileFactory) {
    $scope.profile = {};

    ProfileFactory.query(function(data){
      console.log(data)
      $scope.profile = data.object;
    });
  }])
  /*

    Handle the corpus list view.
    ===
  
  */
  .controller('corpusListCtrl', ['$scope', 'CorpusListFactory', function($scope, CorpusListFactory) {
    $scope.items = [];
    $scope.status = CONTROLLER_STATUS_WORKING;

    CorpusListFactory.query(function(data){
      console.log(data)
      $scope.howmany = data.meta.total_count;
      $scope.items = data.objects;
      $scope.status = CONTROLLER_STATUS_AVAILABLE;
    });

    $scope.addTodo = function(){
      if($scope.status != CONTROLLER_STATUS_AVAILABLE)
        return;
      $scope.status = CONTROLLER_STATUS_WORKING;

      CorpusListFactory.save({}, {
        name: $scope.name,
      }, function(data){
        $scope.status = CONTROLLER_STATUS_AVAILABLE;
        $scope.items = data.objects;
      });
    }
  }])
  /*
    
    Single corpus controller.
    ===

    COntrol the JOB flow: status, start stop for the current corpus, if any.

  */
  .controller('corpusCtrl', ['$scope','$upload','$routeParams','CorpusFactory', 'DocumentListFactory', 'CommandFactory', function($scope, $upload, $routeParams, CorpusFactory, DocumentListFactory, CommandFactory) {
    CorpusFactory.query({id: $routeParams.id}, function(data){
      $scope.corpus = data.object;
      
    });
    DocumentListFactory.query({id: $routeParams.id}, function(data){
      $scope.howmany = data.meta.total_count;
      $scope.documents = data.objects;
    });

    // start command if the corpus is job free and if the global scope is free of actions
    $scope.startHarvest = function(){
      $scope.toast({message:"launching harvesting!"});
      CommandFactory.launch({cmd:'harvest', id:$scope.corpus.id}, function(data){
        console.log(data);
        $scope.toast({message:"harvesting launghed"});
      
      });
    };
    
    $scope.onFileSelect = function($files) {
      //$files: an array of files selected, each file has name, size, and type.
      for (var i = 0; i < $files.length; i++) {
        var file = $files[i];
        $scope.upload = $upload.upload({
          url: '/api/corpus/' + $scope.corpus.id + '/upload', //upload.php script, node.js route, or servlet url
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
          console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
        }).success(function(data, status, headers, config) {
          // file is uploaded successfully
          console.log(data);
          DocumentListFactory.query({id: $routeParams.id}, function(data){
      $scope.howmany = data.meta.total_count;
      $scope.documents = data.objects;
    });
        });
        //.error(...)
        //.then(success, error, progress); 
      }
    // $scope.upload = $upload.upload({...}) alternative way of uploading, sends the the file content directly with the same content-type of the file. Could be used to upload files to CouchDB, imgur, etc... for HTML5 FileReader browsers. 
  };
  }])
  /* 
    
    Document Controller (show)
    ===

  */
  .controller('documentCtrl', ['$scope', '$routeParams', 'DocumentFactory', 'DocumentSegmentsFactory', function($scope, $routeParams, DocumentFactory, DocumentSegmentsFactory) {
    $scope.corpus = {};
    $scope.document = {};
    $scope.segments = [];

    DocumentFactory.query({id: $routeParams.id}, function(data){
      $scope.document = data.object;
      $scope.corpus = data.object.corpus;

      DocumentSegmentsFactory.query({id: $routeParams.id}, function(data){
        console.log(data);
        $scope.segments = data.objects
      })
    })
  }]);