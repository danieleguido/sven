'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:DocumentCtrl
 * @description
 * # DocumentCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('DocumentCtrl', function ($scope, $log, $filter, $location, $routeParams, DocumentFactory, DocumentsConceptsFactory) {
    $scope.document = {
      date: new Date()
    };

    $routeParams.id && DocumentFactory.query({id: $routeParams.id}, function(data){
      console.log(data);
      $scope.document = data.object;
      // once done load segments
    
    });



    $scope.save = function() {
      var doc = angular.copy($scope.document);
      $log.info('DocumentCtrl saving ', angular.copy($scope.document))
      DocumentFactory.save({
        id: doc.id,
        name: doc.name,
        date: $filter('date')($scope.document.date, 'yyyy-MM-dd'),//$scope.document.date,
        abstract: doc.abstract
      }, function(res) {
        console.debug('DocumentCtrl saved',res);
        $scope.document = res.object;
        if(res.status == 'ok') {
          toast('saved');
          $location.path('/document/' + res.object.id);
        }
        
      });
    };

    // datepicker
    $scope.openDatePicker = function($event) {
      $event.preventDefault();
      $event.stopPropagation();
      $scope.opened = true;
    };

    /*
      SEGMENTS PART 
      ===
    */
    $scope.measure = 'tf';
    $scope.$parent.limit = 50;

    $scope.$parent.orderBy.choices = [
        {label:'tf', value:'tf DESC'},
        {label: 'tfidf', value:'tfidf DESC'},
        {label: 'top shared TF', value:'distribution DESC|tf DESC'},
        {label:'by name a-z', value:'cluster ASC'}
      ];
    $scope.$parent.orderBy.choice = {label: 'top shared TF', value:'distribution DESC|tf DESC'};
    
    $scope.sync = function() {
      DocumentsConceptsFactory.query(
        $scope.getParams({
          id:$routeParams.id
        }), function(data){
          console.log(data); // pagination needed
          $scope.totalItems = data.meta.total_count;
          $scope.clusters = data.objects;
          $scope.groups = [];
        });
    };

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.debug('ConceptsCtrl @API_PARAMS_CHANGED');
      $scope.sync();
    });

    $scope.sync();

    
  });
