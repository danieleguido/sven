'use strict';

var CONTROLLER_STATUS_AVAILABLE = 'available',
    CONTROLLER_STATUS_WORKING = 'busy',
    CONTROLLER_PARAMS_UPDATED = "CONTROLLER_PARAMS_UPDATED";

/* Controllers */

angular.module('sven.controllers', ['angularFileUpload'])
  /*

    Contains shared jquery plugin, like window-related plugin (toastmessage)
    ===
    
    Handle with care, and try not to override them locally.
  */
  .controller('initCtrl', ['$scope', '$rootScope', '$location', '$route', function($scope, $rootScope, $location, $route) {
    /*
      filters application varies according to the controller!!!!!!! beware.
      @todo ctrlspecific limit, offsets and filters?
    */
    $rootScope.filters = {};
    $rootScope.limit = 25;
    $rootScope.offset = 0;

    $rootScope.loadFilters = function(options) {
      var candidates = $location.search().filters,
          limit = +$location.search().limit,
          offset = +$location.search().offset;

      if(candidates) {
        try{
          var filters = JSON.parse(candidates);
          $rootScope.filters = filters;
        } catch(e){
          console.log("%c! filters failed ", 'color:white; background-color:crimson', e.message);
          
        }
      } else
        $rootScope.filters = {};

      $rootScope.limit = isNaN(limit)? $rootScope.limit: limit;
      $rootScope.offset = isNaN(offset)? $rootScope.offset: offset;
      // limit and offset here
      $rootScope.$broadcast(CONTROLLER_PARAMS_UPDATED, options);
    };

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

    $rootScope.toast({message:"welcome to sven", stayTime: 3000});

    $scope.$on('$routeUpdate', function(e, r){
      $scope.loadFilters({controller: r.$$route.controller}); // push current controllername
    });

    $rootScope.loadFilters();
    console.log('> initCtrl ready');
  }])

  /*

    Handle the main view. Unused
    ===
  
  */
  .controller('indexCtrl', ['$scope', function($scope) {
    console.log('> indexCtrl ready');
  }])
  /*
    
    System status controller
    ====

  */
  .controller('notificationCtrl', ['$rootScope', 'NotificationFactory', '$timeout', function($rootScope, NotificationFactory, $timeout) {
    //console.log('load notificationCtrl')
    $rootScope.notification = {};
    $rootScope.activity = '.';
    // ugly ajax polling...
    (function tick() {
        $rootScope.activity = '..';

        NotificationFactory.query(function(data){
          $rootScope.activity = '...';
          $rootScope.notification = data;
          $timeout(tick, 4617);
        });
    })();
    console.log('> notificationCtrl ready');
  }])
  /*
    
    System log controller (cfr. notificationCtrl)
    ====

  */
  .controller('logCtrl', ['$rootScope', '$scope', function($rootScope, $scope){
    console.log('> logCtrl ready');
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
    console.log('> profileCtrl ready');
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

    $scope.showCreate = function(){
      $('#create-corpus-form').addClass("opened")
    };

    $scope.addTodo = function(){
      if($scope.status != CONTROLLER_STATUS_AVAILABLE)
        return;
      $scope.status = CONTROLLER_STATUS_WORKING;
      $('#create-corpus-form').removeClass("opened")
      CorpusListFactory.save({}, {
        name: $scope.name,
      }, function(data){
        $scope.status = CONTROLLER_STATUS_AVAILABLE;
        $scope.items = data.objects;
      });
    };
    console.log('> corpusListCtrl ready');
  }])
  /*
    
    Single corpus controller.
    ===

    COntrol the JOB flow: status, start stop for the current corpus, if any.

  */
  .controller('corpusCtrl', ['$rootScope', '$scope','$upload','$routeParams','CorpusFactory', 'DocumentListFactory', 'CommandFactory', function($rootScope, $scope, $upload, $routeParams, CorpusFactory, DocumentListFactory, CommandFactory) {
    // search for corpus job status among running jobs
    $scope.attachJob = function(){
      if($scope.corpus && $scope.notification.objects){
        $scope.corpus.job = $scope.notification.objects.filter(function(d){return d.corpus==$scope.corpus.id}).pop();
        
      }
    };

    $rootScope.setCorpus = function(id){
      console.log('$rootScope.setCorpus', id);
      CorpusFactory.query({id: id}, function(data){
        $rootScope.corpus = data.object;
        console.log('$rootScope.setCorpus',  data.object);
        $scope.notification && $scope.attachJob()
      });
    };

    // start command if the corpus is job free and if the global scope is free of actions
    $scope.start = function(cmd){
      $scope.toast({message:"starting " + cmd});
      CommandFactory.launch({cmd:cmd, id:$scope.corpus.id}, function(data){
        console.log(data);
        $scope.toast({message: cmd + "started"});
      
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

    $rootScope.$watch('notification', $scope.attachJob, true);
    
    console.log('> corpusCtrl ready');
  }])
  /* 
    
    Document Controller (show)
    ===

  */
  .controller('documentCtrl', ['$scope', '$routeParams', 'DocumentFactory', 'DocumentSegmentsFactory', function($scope, $routeParams, DocumentFactory, DocumentSegmentsFactory) {
    $scope.document = {};
    $scope.segments = [];


    DocumentFactory.query({id: $routeParams.id}, function(data){
      $scope.document = data.object;
      $scope.setCorpus(data.object.corpus.id);

      DocumentSegmentsFactory.query({id: $routeParams.id}, function(data){
        console.log(data);
        $scope.segments = data.objects
      })
    });



    console.log('> documentCtrl ready');
  }])
  .controller('documentListCtrl', ['$scope', '$rootScope', '$routeParams', 'DocumentListFactory',  function($scope, $rootScope, $routeParams, DocumentListFactory) {
    
    $rootScope.setCorpus($routeParams.id);

    $scope.sync = function() {
      DocumentListFactory.query({id: $routeParams.id, limit:$scope.limit, offset:$scope.offset, filters:$scope.filters}, function(data){
          $scope.howmany = data.meta.total_count;
          $scope.documents = data.objects;
      });
    };

    $scope.$on(CONTROLLER_PARAMS_UPDATED, function(e, options) {

      console.log('received...');
      $scope.sync();
    });

    $scope.sync();
    console.log('> documentListCtrl ready');
  }])
  /* 
    
    Segment Controller (list)
    ===

  */
  .controller('segmentListCtrl', ['$scope', '$routeParams', 'SegmentListFactory', function($scope, $routeParams, SegmentListFactory) {
    $scope.segments = [];
    
    $scope.setCorpus($routeParams.id);

    SegmentListFactory.query({id: $routeParams.id}, function(data){
      $scope.segments = data.objects;
    });
    console.log('> segmentListCtrl ready');
  }])
  /* 
    
    Filter Controller (list)
    ===

  */

  .controller('filtersCtrl', ['$scope', function($scope) {
    console.log('> filterstCtrl ready');
  }])


