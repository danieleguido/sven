'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:DocumentsCtrl
 * @description
 * # DocumentsCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('DocumentsCtrl', function ($scope, $log, $location, DocumentsFactory) {
    $scope.document = {}// new document
    $scope.items = []; // current list of items

    $log.debug('DocumentsCtrl ready on corpus:', $scope.$parent.corpus.name||'not set');
    
    $scope.awesomeThings = [
      'HTML5 Boilerplate',
      'AngularJS',
      'Karma'
    ];

    if($scope.$parent.corpus.id) {
      // wait for corpus...
      DocumentsFactory.query({id:1}, function(data){
        $log.info('loading documents', data);
        $scope.items = data.objects;
      }, function(){

      });
    }


    console.log($scope.$parent.corpus.name);

    $scope.saveUrl = function() {
      $log.info('saveUrl: ', $scope.document.url);
      DocumentsFactory.save({
        id: $scope.$parent.corpus.id
      },{
        mimetype: 'text/html',
        name: $scope.document.url
          .replace(/http:\/\/w+/g,'')
          .replace(/[^\w]/g, ' ')
          .replace(/\s+/g,' ')
          .trim().substring(0,64),
        url:$scope.document.url
      }, function(data) {
        console.log(data);
        data.object && $location.path('/document/' + data.object.id);
      });
    };




    /* order by dropdown */
    $scope.orderBy = {
      choices: [
        {label:'by date added', value:'id'},
        {label:'by date', value:'date'},
        {label:'by name', value:'name'}
      ],
      choice: {label:'by date added', value:'id'},
      label: 'by date added',
      isopen: false,
      direction: true // a-z or false z-a
    };

    $scope.switchOrderBy = function(choice) {
      $log.info('switchOrderBy', choice)
      $scope.orderBy.choice = choice;
      $scope.orderBy.isopen = false;
    };

    


    $scope.status = {
      isopen: false
    };


  $scope.totalItems = 64;
  $scope.currentPage = 4;

  $scope.setPage = function (pageNo) {
    $scope.currentPage = pageNo;
  };

  $scope.pageChanged = function() {
    console.log('Page changed to: ' + $scope.currentPage);
  };

  $scope.maxSize = 5;
  $scope.bigTotalItems = 175;
  $scope.bigCurrentPage = 1;

  });
