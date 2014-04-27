'use strict';

var CTRL_LOADED = 'background: lime; color: #181818';


angular.module('sven.controllers', [])
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
  .controller('documentListCtrl', ['$scope', '$routeParams', 'DocumentListFactory', function($scope, $routeParams, DocumentListFactory) {
    
    $scope.sync = function() {
      DocumentListFactory.query({id: $routeParams.id, limit:$scope.limit, offset:$scope.offset, filters:$scope.filters}, function(data){
          console.log(data);
          $scope.items = data.objects;
          $scope.paginate({
            total_count: data.meta.total_count
          });
      });
    };

    $scope.sync();
    console.log('%c documentListCtrl ', CTRL_LOADED);
  }])
  .controller('contextCtrl', ['$scope', function($scope) {


  }])
  .controller('blankCtrl', ['$scope', function($scope) {


  }])