'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:NetworkCtrl
 * @description
 * # NetworkCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('StreamCtrl', function ($scope, $log, $routeParams, concepts) {
    $log.debug('StreamCtrl ready', concepts);
    // $scope.graph = graph
    $scope.concepts = concepts.objects;
  })