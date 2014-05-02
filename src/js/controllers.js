'use strict';

var CTRL_LOADED = 'background: lime; color: #181818',
    STYLE_INFO = 'color: #b8b8b8',
    CONTROLLER_PARAMS_UPDATED = "CONTROLLER_PARAMS_UPDATED",

    gimmesize = function(obj) {
      var obj = angular.copy(obj),
          size = 0,
          key;

      for (key in obj) {
        if (obj.hasOwnProperty(key))
          size++;
      };
      return size;
    };



angular.module('sven.controllers', ['angularFileUpload'])
  /*
    
    The very main controller. Handle django orm filters in ng-view .
    ===
    
    limit and offset of the curtrent view are also set.
  */
  .controller('layoutCtrl', ['$scope', '$rootScope','$location', '$route', function($scope, $rootScope, $location, $route) {

    $scope.limit = 25;
    $scope.offset= 0;
    $scope.default_limit = 25;
    $scope.default_offset = 0;
    
    $scope.filters = {};
    $scope.query = {};
    
    $scope.numofpages = 0;
    $scope.page = 0;
    console.log('%c layoutCtrl ', CTRL_LOADED);
    
    // look after the current corpus, babe.
    $rootScope.corpus = {};
    $scope.follow = function(link) {
      //alert(link)
      var path = Array.prototype.slice.call(arguments).join('/').replace(/\/+/g,'/');
      $location.path(path);
    }
    
    $scope.search = function() {
      console.log("%c search ", 'color:white; background-color:#383838', $scope.query);
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset;
      $location.search({
        'search': $scope.query
      });
    }

    $scope.pageto = function(page) {
      var page = Math.max(0, Math.min(page, $scope.numofpages));
      console.log('page to', page);
      $scope.offset = page * $scope.limit;
      $scope.distill();
    };


    $scope.nextPage = function() {
      $scope.pageto(+$scope.page + 1);
    };
            

    $scope.prevPage = function() {
      $scope.pageto(+$scope.page - 1);
    };


    $scope.paginate = function(options) {
      var options = options || {},
          pages = [],
          left = 0,
          right = 0;

      $scope.total_count = options.total_count;
      console.log('$scope.paginate', $scope.limit, $scope.offset);
      
      $scope.numofpages = Math.floor(($scope.total_count-1) / $scope.limit );
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
    };


    $scope.distill = function(options) {
      var candidates = $location.search().filters,
          query = $location.search().search;

      if(query) {
        $scope.query = query;
      };

      if(candidates) {
        try{
          var filters = JSON.parse(candidates);
          $scope.filters = filters;
        } catch(e){
          console.log("%c! distill: filters failed ", 'color:white; background-color:crimson', e.message);
          
        }
      } else {
        $scope.filters = {};
      }

      $scope.howmanyfilters = gimmesize($scope.filters);

      console.log("%c distill: loading filters ", 'color:white; background-color:green', 'query:',$scope.query, $scope.offset, $scope.limit);   
      $scope.$broadcast(CONTROLLER_PARAMS_UPDATED, options);
    };


    $scope.setProperties = function(property, value) {
      $scope.filters[property] = [value];
      console.log('%c filters setProperties', STYLE_INFO, property, value, $scope.filters);
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset,
        
      $location.search({
        'filters': JSON.stringify($scope.filters)
      });
    };


    $scope.setProperty = function(property, value) {
      $scope.filters[property] = value;
      console.log('%c filters setProperty', 'background: crimson; color: white',property, value, $scope.filters);
      $location.search('filters', JSON.stringify($scope.filters))
    };


    $scope.removeProperty = function(property, value) {
      console.log('removing', property, value, 'from filters');
      delete $scope.filters[property];
      $location.search({
        'filters': JSON.stringify($scope.filters)
      });
    }


    $scope.extendFilters = function(filter) {
      var filters = angular.extend({}, $scope.filters, filter);
      return JSON.stringify(filters)
    };

    // LISTENERS
    $rootScope.$on('$routeChangeSuccess', function(e, r){
      console.log("%c    route change success", STYLE_INFO);
      $scope.filters = {};
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset;
      $scope.distill(); // reload filters directly form the params
    });


    $rootScope.$on('$routeUpdate', function(e, r){
      console.log("%c route updated", STYLE_INFO);
      $scope.distill({controller: r.$$route.controller}); // push current controllername
    });
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

    $scope.$on(CONTROLLER_PARAMS_UPDATED, function(e, options) {
      $scope.sync();
    });

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