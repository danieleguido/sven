'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('MainCtrl', function ($scope) {
    $scope.awesomeThings = [
      'HTML5 Boilerplate',
      'AngularJS',
      'Karma'
    ];
  });
