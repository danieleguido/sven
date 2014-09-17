'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:DocumentCtrl
 * @description
 * # DocumentCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('DocumentCtrl', function ($scope, $routeParams, DocumentFactory) {
    $scope.document = {};
    $routeParams.id && DocumentFactory.query({id: $routeParams.id}, function(data){
      console.log(data);
      $scope.document = data.object
    });
  });
