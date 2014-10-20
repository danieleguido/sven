'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:DocumentCtrl
 * @description
 * # DocumentCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('DocumentCtrl', function ($scope, $log, $filter, $location, $routeParams, DocumentFactory) {
    $scope.document = {
      date: new Date()
    };

    $routeParams.id && DocumentFactory.query({id: $routeParams.id}, function(data){
      console.log(data);
      $scope.document = data.object
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
  });
